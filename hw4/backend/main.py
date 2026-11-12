"""Campus Customs Shop API.

A small FastAPI backend that reads products, sizes and stock from
data/campus_customs.db and serves the product images. Product and stock
lookups open the database read-only. The only writes are new customer
accounts, which are handled in backend/auth.py. The chat endpoint hands
messages to the PydanticAI agent in backend/agent.py.

Run from the backend folder:
    ../.venv/bin/uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import AgentNotConfigured, AgentUnavailable, model_name, run_chat
from quick_answers import try_quick_answer
from auth import current_user, router as auth_router
import audit
import memory
from models import ChatHistoryResponse, ChatMessage, ChatRequest, ChatResponse, CustomerInfo
from tools import ChatDeps, _to_card, clean_description, filter_catalogue, search_catalogue

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s: %(message)s")
log = logging.getLogger("campus_customs")

HW4_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = HW4_DIR / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
IMAGES_DIR = DATA_DIR / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# The garment_type labels in the catalogue are inconsistent ("hoodie",
# "pullover hoodie", "full-zip hooded sweatshirt"...), so group them into a
# few shopper-friendly categories. Order matters: first match wins.
CATEGORY_RULES = [
    ("Quarter-Zips", ("quarter-zip",)),
    ("Jackets & Fleece", ("jacket", "fleece")),
    ("Hoodies", ("hood",)),
    ("Long Sleeves", ("long-sleeve",)),
    ("Crewnecks", ("crewneck", "mockneck")),
    ("T-Shirts", ("t-shirt",)),
]
CATEGORY_NAMES = [name for name, _ in CATEGORY_RULES]

app = FastAPI(title="Campus Customs Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth_router)
memory.ensure_schema()
audit.ensure_file()

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


def connect() -> sqlite3.Connection:
    """Open the database in read-only mode."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def category_for(garment_type: str) -> str:
    text = garment_type.lower()
    for name, keywords in CATEGORY_RULES:
        if any(k in text for k in keywords):
            return name
    return "Other"


def image_url(image_file_path: str) -> str:
    # Stored as "products/<file>.jpg", relative to data/.
    return "/images/" + Path(image_file_path).name


def product_summary(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": category_for(row["garment_type"]),
        "description": clean_description(row["description"]),
        "colors": json.loads(row["colors"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
        "total_stock": row["total_stock"] if "total_stock" in row.keys() else row["total_quantity"],
    }


PRODUCT_SELECT = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
    FROM catalogue c
    LEFT JOIN inventory i ON i.product_id = c.product_id
"""


@app.get("/api/health")
def health() -> dict:
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]
    return {"status": "ok", "products": count, "model": model_name()}


@app.get("/api/categories")
def categories() -> list[str]:
    return CATEGORY_NAMES


@app.get("/api/products")
def list_products(
    q: str | None = Query(None, description="Search name, description, colors and tags"),
    category: str | None = None,
    size: str | None = Query(None, description="Only products in stock in this size (XS–XXL)"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
) -> list[dict]:
    # Same matching and filters the chatbot uses, so "hoodies", "tees" or "1/4 zip" all work.
    rows, _ = filter_catalogue(
        DB_PATH, q=q, category=category or None, size=size or None, min_price=min_price, max_price=max_price
    )
    products = [product_summary(r) for r in rows]
    products.sort(key=lambda p: p["name"])
    return products


@app.get("/api/sizes")
def sizes() -> list[str]:
    return SIZE_ORDER


@app.get("/api/price-range")
def price_range() -> dict:
    with connect() as conn:
        lo, hi = conn.execute("SELECT MIN(price), MAX(price) FROM catalogue").fetchone()
    return {"min": lo, "max": hi}


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with connect() as conn:
        row = conn.execute(
            PRODUCT_SELECT + " WHERE c.product_id = ? GROUP BY c.product_id",
            (product_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        size_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?",
            (product_id,),
        ).fetchall()

    sizes = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in size_rows),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )
    product = product_summary(row)
    product["search_tags"] = json.loads(row["search_tags"])
    product["sizes"] = sizes
    return product


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(request: Request) -> ChatHistoryResponse:
    """The logged-in customer's own saved conversation. Guests get 401.
    The user id comes only from the signed session cookie."""
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to see your saved chats.")
    return ChatHistoryResponse(messages=memory.load_history(user["id"]))


FALLBACK_MESSAGES = {
    "timeout": "Sorry, I'm taking longer than usual to answer.",
    "busy": "Sorry, our assistant is really busy right now.",
    "offline": "Sorry, our assistant is having trouble connecting right now.",
    "config": "Sorry, our assistant isn't available at the moment.",
    "limit": "Sorry, that question needed more steps than I'm allowed to take.",
    "error": "Sorry, something went wrong on my end.",
}


def _friendly_fallback(kind: str, text: str, deps: ChatDeps) -> str:
    """A kind reply when the AI can't answer. If the message looks like a product
    search, still show matching products straight from the database."""
    opener = FALLBACK_MESSAGES.get(kind, FALLBACK_MESSAGES["error"])
    # Forget anything a half-finished AI attempt put on screen.
    deps.searched, deps.shown_products, deps.shown_query, deps.shown_total, deps.shown_see_all = False, [], None, 0, None
    rows, total, unmatched = search_catalogue(deps.db_path, text, limit=12)
    if rows and not unmatched and total <= 40:
        deps.searched = True
        deps.shown_products = [_to_card(r) for r in rows]
        deps.shown_query = text.strip().rstrip("?.!")[:60]
        deps.shown_total = total
        deps.shown_see_all = None
        return (
            f"{opener} In the meantime, I found {total} matching "
            f"{'product' if total == 1 else 'products'} in our catalogue and put "
            f"{'it' if total == 1 else 'them'} on the page for you. Please try your question again in a moment."
        )
    return (
        f"{opener} Please try again in a moment. You can still browse everything on Products (/products), "
        "and every product page shows live prices and sizes."
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """Run the customer's message through the PydanticAI shopping assistant."""
    latest = body.messages[-1]
    if latest.role != "user":
        raise HTTPException(status_code=422, detail="The last message must come from the customer.")
    text = memory.redact(latest.content)

    user = current_user(request)
    if user:
        # Logged in: use their saved history from the database, not what the browser sent.
        earlier = [
            ChatMessage(role=m.role, content=m.content)
            for m in memory.load_history(user["id"], limit=memory.HISTORY_FOR_AGENT)
        ]
        customer = CustomerInfo(first_name=user["first_name"], last_name=user["last_name"], email=user["email"])
    else:
        # Guest: use the messages from this browser tab only. Nothing is saved.
        earlier = [ChatMessage(role=m.role, content=memory.redact(m.content)) for m in body.messages[:-1]]
        customer = None

    deps = ChatDeps(customer=customer, page=body.page)
    started = time.perf_counter()

    # 1) Very simple questions ("What hoodies do you have?") are answered straight
    #    from the database: instant, and no AI call needed.
    reply = try_quick_answer(text, deps)
    answered_by = "database"
    tool_calls: list[dict[str, str]] = []
    stop_reason = "completed: answered instantly from the database (no AI call needed)"
    model_requests = 0
    if reply is not None:
        tool_calls = [{
            "tool": "quick_answer",
            "arguments": audit.clean(f"category={deps.shown_query!r}" if deps.searched else f"price check, page={body.page.path if body.page else '/'}", 160),
            "result": audit.clean(
                f"{deps.shown_total} match(es), {len(deps.shown_products)} shown as cards" if deps.searched else reply, 160
            ),
        }]

    # 2) Everything else goes to the PydanticAI agent.
    if reply is None:
        answered_by = "ai"
        try:
            outcome = await run_chat(text, earlier, deps)
            reply, tool_calls = outcome.reply, outcome.tool_calls
            stop_reason, model_requests = outcome.stop_reason, outcome.model_requests
        except AgentNotConfigured:
            log.error("Chat is not configured: the AI provider key is missing.")
            reply, answered_by = _friendly_fallback("config", text, deps), "fallback"
            stop_reason = "stopped: the AI provider isn't configured (missing key); sent a friendly fallback"
        except AgentUnavailable as exc:
            log.warning("AI unavailable (%s: %s); using fallback reply.", exc.kind, exc)
            reply, answered_by = _friendly_fallback(exc.kind, text, deps), "fallback"
            stop_reason = {
                "limit": "stopped: hit the agent's request/tool-call limit; sent a friendly fallback",
                "timeout": "stopped: the AI took too long (timeout); sent a friendly fallback",
                "busy": "stopped: the AI service was busy (rate limit); sent a friendly fallback",
                "offline": "stopped: couldn't reach the AI service; sent a friendly fallback",
                "config": "stopped: the AI service rejected the configuration; sent a friendly fallback",
            }.get(exc.kind, "stopped: unexpected AI error; sent a friendly fallback")
            if deps.searched:
                tool_calls = [{
                    "tool": "fallback_catalogue_search",
                    "arguments": audit.clean(f"query={text!r}", 160),
                    "result": f"{deps.shown_total} match(es), {len(deps.shown_products)} shown as cards",
                }]

    elapsed = time.perf_counter() - started
    log.info("chat answered by %s in %.2fs", answered_by, elapsed)
    audit.record(
        answered_by=answered_by,
        stop_reason=stop_reason,
        tool_calls=tool_calls,
        question=text,
        reply=reply,
        logged_in=user is not None,
        page_path=body.page.path if body.page else None,
        duration_seconds=elapsed,
        model_requests=model_requests,
    )

    reply = memory.redact(reply)
    # Save real answers only. A "sorry, try again" reply isn't worth remembering.
    if user and answered_by != "fallback":
        memory.save_message(user["id"], "user", text)
        memory.save_message(user["id"], "assistant", reply, deps.shown_products)

    return ChatResponse(
        reply=reply,
        answered_by=answered_by,
        searched=deps.searched,
        products=deps.shown_products,
        search_query=deps.shown_query,
        total_matches=deps.shown_total,
        see_all_path=deps.shown_see_all,
    )
