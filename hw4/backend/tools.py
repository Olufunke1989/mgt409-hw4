"""Tools the Campus Customs chatbot can call.

Every fact a tool returns comes from verified store details or straight from
data/campus_customs.db. The database is always opened read-only here.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from urllib.parse import quote, urlencode
from pathlib import Path

from pydantic_ai import RunContext

import json
import re

from models import (
    CategorySummary,
    CustomerInfo,
    InventoryResult,
    NotFound,
    PageContext,
    ProductDetails,
    ProductCard,
    ProductMatch,
    ProductSearchResult,
    Recommendation,
    RecommendationResult,
    SitePage,
    SizeAvailability,
    StoreInfo,
)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs.db"

# Same grouping the website's category filters use (see main.py).
CATEGORY_RULES = [
    ("Quarter-Zips", ("quarter-zip",)),
    ("Jackets & Fleece", ("jacket", "fleece")),
    ("Hoodies", ("hood",)),
    ("Long Sleeves", ("long-sleeve",)),
    ("Crewnecks", ("crewneck", "mockneck")),
    ("T-Shirts", ("t-shirt",)),
]


CATEGORY_NAMES = [name for name, _ in CATEGORY_RULES]


def category_for(garment_type: str) -> str:
    text = garment_type.lower()
    for name, keywords in CATEGORY_RULES:
        if any(k in text for k in keywords):
            return name
    return "Other"


@dataclass
class ChatDeps:
    """Per-request context handed to every tool."""

    db_path: Path = DB_PATH
    # From the signed session cookie, never from chat text (Problem 8).
    customer: CustomerInfo | None = None
    # The page the customer is viewing (sent by the website).
    page: PageContext | None = None
    # Filled in by search_products so the website can show product cards.
    searched: bool = False
    shown_products: list[ProductCard] = field(default_factory=list)
    shown_query: str | None = None
    shown_total: int = 0
    shown_see_all: str | None = None


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- general store tools ----------

def get_store_info(ctx: RunContext[ChatDeps]) -> StoreInfo:
    """Get verified facts about Campus Customs: name, location, website and what it sells.
    Use this for general questions about the store. Anything listed in unknown_topics
    is not known, so tell the customer you don't have that information."""
    return StoreInfo(
        name="Campus Customs",
        address="57 Broadway, New Haven, CT",
        online_store="yalebulldogblue.com",
        what_we_sell=(
            "Officially licensed Yale apparel: hoodies, crewneck sweatshirts, T-shirts, "
            "quarter-zips, jackets and fleece, and long-sleeve shirts, in sizes XS to XXL."
        ),
        unknown_topics=[
            "store hours",
            "phone number",
            "shipping times and costs",
            "return and exchange policy",
            "discounts, sales and promo codes",
            "custom orders",
        ],
    )


def get_website_guide(ctx: RunContext[ChatDeps]) -> list[SitePage]:
    """List the pages on this website and what each is for. Use this to help customers
    find their way around (browsing, searching, product pages, accounts)."""
    return [
        SitePage(name="Home", path="/", what_it_is_for="Featured picks, shop-by-category tiles and our store location."),
        SitePage(
            name="Products",
            path="/products",
            what_it_is_for=(
                "The full catalogue. Customers can search by keyword (college, sport, color), "
                "filter by category and sort by name or price."
            ),
        ),
        SitePage(
            name="Product page",
            path="/products/<product id>",
            what_it_is_for="Click any product card to see a large photo, full description, price, colors and stock by size.",
        ),
        SitePage(name="About Us", path="/about", what_it_is_for="Our story and what makes Campus Customs different."),
        SitePage(name="Log In", path="/login", what_it_is_for="Log in to an existing account."),
        SitePage(name="Create Account", path="/signup", what_it_is_for="Make a new customer account."),
    ]


def list_product_categories(ctx: RunContext[ChatDeps]) -> list[CategorySummary]:
    """Count how many products the catalogue has in each category (from the database)."""
    with connect(ctx.deps.db_path) as conn:
        rows = conn.execute("SELECT garment_type FROM catalogue").fetchall()
    counts: dict[str, int] = {}
    for r in rows:
        cat = category_for(r["garment_type"])
        counts[cat] = counts.get(cat, 0) + 1
    return [CategorySummary(category=c, product_count=n) for c, n in sorted(counts.items())]



# ---------- product and inventory tools (Problem 6) ----------

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK = 3
MAX_MATCHES = 8

# Different ways customers say the same size.
SIZE_ALIASES = {
    "xs": "XS", "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "double xl": "XXL", "extra extra large": "XXL",
}

# Words that don't help tell products apart.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "for", "in", "on", "with", "to", "do", "you", "have", "has", "any", "your",
    "what", "which", "show", "me", "is", "it", "this", "that", "how", "much", "many", "price", "cost", "costs",
    "available", "availability", "stock", "sell", "carry", "got", "some", "one", "ones", "item", "items", "product",
    "products", "please", "i", "im", "looking", "want", "need", "find", "yale", "campus", "customs", "size", "sizes",
    "small", "medium", "large", "xl", "xxl", "xs", "are", "there", "can", "get", "about", "like", "see",
    "residential", "college", "merch", "merchandise", "apparel", "clothing", "gear", "something", "anything",
    "gift", "gifts", "present", "presents", "idea", "ideas", "recommend", "recommendation", "suggestion",
    "suggestions", "nice", "good", "great", "cool", "cute", "budget", "cheap", "affordable", "under", "over",
}

# A searched word can also match these words in the catalogue.
SYNONYMS = {
    "sweatshirt": {"sweatshirt", "crewneck", "hoodie"},
    "sweater": {"sweater", "sweatshirt", "crewneck", "fleece"},
    "jumper": {"crewneck", "sweatshirt"},
    "pullover": {"pullover", "hoodie", "quarterzip"},
    "top": {"tshirt", "crewneck", "longsleeve"},
    "shirt": {"tshirt", "longsleeve", "shirt"},
    "coat": {"jacket", "fleece"},
    "jacket": {"jacket", "fleece", "bomber"},
    "grey": {"gray"},
    "zip": {"zip", "quarterzip", "fullzip"},
    "warm": {"fleece", "hoodie", "jacket", "quarterzip", "sweatshirt"},
    "cozy": {"fleece", "hoodie", "sweatshirt"},
    "winter": {"fleece", "hoodie", "jacket", "quarterzip"},
}


# Words for a *kind* of item. These only count when they appear in the product's
# name or garment type; a "sailor hat" graphic tag doesn't make a hoodie a hat.
GARMENT_WORDS = {
    "hat", "cap", "beanie", "scarf", "mug", "sock", "glove", "mitten", "blanket", "bag", "tote", "pant", "short",
    "jogger", "legging", "polo", "jacket", "hoodie", "crewneck", "tshirt", "quarterzip", "fullzip", "longsleeve",
    "sweatshirt", "sweater", "fleece", "vest", "pennant", "sticker", "decal", "keychain", "bottle", "umbrella",
    "warm", "cozy", "winter",
}


def normalize(text: str) -> str:
    """Lowercase and merge the different spellings used for the same garment."""
    t = text.lower()
    t = re.sub(r"\b(t[\s-]?shirts?|tees?)\b", "tshirt", t)
    t = re.sub(r"\b(hoodies?|hooded|hoods?)\b", "hoodie", t)
    t = re.sub(r"\b(1\s*/\s*4|1\s+4|quarter)[\s-]*zips?\b", "quarterzip", t)
    t = re.sub(r"\bfull[\s-]*zips?\b", "fullzip", t)
    t = re.sub(r"\bcrew[\s-]*necks?\b", "crewneck", t)
    t = re.sub(r"\blong[\s-]*sleeves?\b", "longsleeve", t)
    t = re.sub(r"\bgrey\b", "gray", t)
    return t


def words(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", normalize(text)):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # hoodies -> hoodie, sweatshirts -> sweatshirt
        out.append(w)
    return out


def normalize_size(size: str) -> str | None:
    key = size.strip().lower().replace(".", "")
    if key.upper() in SIZE_ORDER:
        return key.upper()
    return SIZE_ALIASES.get(key)


def stock_status(quantity: int) -> str:
    if quantity <= 0:
        return "sold out"
    return "low stock" if quantity <= LOW_STOCK else "in stock"


def clean_description(text: str) -> str:
    """Hide placeholder text left in the catalogue (3 items say "...filename-based stub")."""
    t = (text or "").strip()
    if "filename-based stub" in t.lower() or "vision blocked" in t.lower():
        return ""
    return t


def short(text: str, limit: int = 140) -> str:
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def _catalogue_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every product with its total stock and the sizes currently in stock."""
    return conn.execute(
        """
        SELECT c.product_id, c.name, c.garment_type, c.description, c.colors, c.search_tags,
               c.image_file_path, c.price,
               COALESCE(SUM(i.quantity), 0) AS total_quantity,
               COALESCE(GROUP_CONCAT(CASE WHEN i.quantity > 0 THEN i.size END), '') AS sizes_in_stock
        FROM catalogue c
        LEFT JOIN inventory i ON i.product_id = c.product_id
        GROUP BY c.product_id
        """
    ).fetchall()


# The word lists used for matching only change if the catalogue changes, so they're
# built once and reused (rebuilt automatically if the database file is modified).
_INDEX_CACHE: dict[str, tuple[float, dict[str, list[tuple[set[str], int]]]]] = {}


def _search_index(db_path: Path, rows: list[sqlite3.Row]) -> dict[str, list[tuple[set[str], int]]]:
    key = str(db_path)
    mtime = db_path.stat().st_mtime
    cached = _INDEX_CACHE.get(key)
    if cached and cached[0] == mtime and len(cached[1]) == len(rows):
        return cached[1]
    index = {
        r["product_id"]: [
            (set(words(r["name"])), 4),
            (set(words(r["garment_type"])), 3),
            (set(words(" ".join(json.loads(r["search_tags"])))), 2),
            (set(words(" ".join(json.loads(r["colors"])))), 2),
            (set(words(r["description"])), 1),
        ]
        for r in rows
    }
    _INDEX_CACHE[key] = (mtime, index)
    return index


def sizes_in_stock(row: sqlite3.Row) -> list[str]:
    have = set(filter(None, (row["sizes_in_stock"] or "").split(",")))
    return [sz for sz in SIZE_ORDER if sz in have]


def _to_match(row: sqlite3.Row) -> ProductMatch:
    return ProductMatch(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        category=category_for(row["garment_type"]),
        price=row["price"],
        colors=json.loads(row["colors"]),
        short_description=short(clean_description(row["description"])) or "No description on file yet.",
        total_quantity=row["total_quantity"],
        in_stock=row["total_quantity"] > 0,
    )


def search_catalogue(db_path: Path, query: str, limit: int = MAX_MATCHES) -> tuple[list[sqlite3.Row], int, list[str]]:
    """Score every catalogue item against the query.

    Returns (best rows, total matches, words that no returned product matched).
    Each meaningful word has to show up in the product's name, type, tags, colors or
    description (or a synonym does). Products matching more of the words rank first,
    and name and type matches count more than description matches. A product found
    only through its description (e.g. "hat" mentioned in passing) doesn't count.
    """
    terms = [w for w in words(query) if w not in STOP_WORDS]
    with connect(db_path) as conn:
        rows = _catalogue_rows(conn)

    # Exact product ID or exact name always wins.
    q = query.strip().lower()
    for r in rows:
        if q in (r["product_id"].lower(), r["name"].lower()):
            return [r], 1, []
    if not terms:
        return [], 0, []

    index = _search_index(db_path, rows)
    scored = []
    for r in rows:
        fields = index[r["product_id"]]
        matched, score, strong = set(), 0, False
        for t in terms:
            options = SYNONYMS.get(t, set()) | {t}
            usable = fields[:2] if t in GARMENT_WORDS else fields  # name + garment type only
            best = max((weight for vocab, weight in usable if vocab & options), default=0)
            if best:
                matched.add(t)
                score += best
                strong = strong or best >= 2
        if matched and strong:
            scored.append((len(matched), score, frozenset(matched), r))

    if not scored:
        return [], 0, terms
    top_hits = max(h for h, _, _, _ in scored)
    best = [(sc, m, r) for h, sc, m, r in scored if h == top_hits]
    best.sort(key=lambda x: (-x[0], x[2]["name"]))
    unmatched = [t for t in terms if t not in best[0][1]]
    return [r for _, _, r in best[:limit]], len(best), unmatched


def find_products(ctx: RunContext[ChatDeps], query: str) -> ProductSearchResult:
    """Look up products in the catalogue by how a customer describes them, e.g.
    "navy crewneck", "Berkeley quarter zip", "Harvard Yale game tee" or "swimming hoodie".
    Returns matching products with product_id, price, colors, total stock and a short
    description. Use the product_id with get_product_details or check_size_availability."""
    rows, total, unmatched = search_catalogue(ctx.deps.db_path, query)
    matches = [_to_match(r) for r in rows]
    if not matches:
        note = "No products matched. Tell the customer politely; do not suggest made-up items."
    elif unmatched:
        note = (
            f"No product matches everything asked for. Nothing matched: {', '.join(unmatched)}. "
            "Say clearly that we don't have that exact item; you may mention these closest matches."
        )
    elif total == 1:
        note = "Exactly one product matched."
    else:
        note = (
            f"{total} products matched (showing up to {MAX_MATCHES}). If the customer asked about one specific "
            "item, ask which one they mean instead of guessing."
        )
    return ProductSearchResult(
        query=query, total_matches=total, matches=matches, unmatched_words=unmatched, note=note
    )


def _sizes(conn: sqlite3.Connection, product_id: str) -> list[SizeAvailability]:
    rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    sizes = [SizeAvailability(size=r["size"], quantity=r["quantity"], status=stock_status(r["quantity"])) for r in rows]
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99)


def get_product_details(ctx: RunContext[ChatDeps], product_id: str) -> ProductDetails | NotFound:
    """Get the full description, price, colors and stock for every size of one product,
    using a product_id from find_products."""
    with connect(ctx.deps.db_path) as conn:
        row = conn.execute(
            """
            SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_quantity
            FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
            WHERE c.product_id = ? GROUP BY c.product_id
            """,
            (product_id,),
        ).fetchone()
        if row is None:
            return NotFound(error=f"No product with id '{product_id}'. Use find_products to look it up first.")
        sizes = _sizes(conn, product_id)
    return ProductDetails(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        category=category_for(row["garment_type"]),
        description=clean_description(row["description"]) or "No description on file yet.",
        colors=json.loads(row["colors"]),
        price=row["price"],
        total_quantity=row["total_quantity"],
        in_stock=row["total_quantity"] > 0,
        sizes=sizes,
        sizes_in_stock=[s.size for s in sizes if s.quantity > 0],
        page_path=f"/products/{row['product_id']}",
    )


def check_size_availability(ctx: RunContext[ChatDeps], product_id: str, size: str) -> InventoryResult | NotFound:
    """Check how many of one product are in stock in one size. Size can be written
    like "M", "medium", "XL", "extra large" or "2XL"."""
    wanted = normalize_size(size)
    if wanted is None:
        return NotFound(error=f"'{size}' isn't a size we carry. Sizes are {', '.join(SIZE_ORDER)}.")
    with connect(ctx.deps.db_path) as conn:
        product = conn.execute("SELECT name, price FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if product is None:
            return NotFound(error=f"No product with id '{product_id}'. Use find_products to look it up first.")
        sizes = _sizes(conn, product_id)
    match = next((s for s in sizes if s.size == wanted), None)
    quantity = match.quantity if match else 0
    return InventoryResult(
        product_id=product_id,
        product_name=product["name"],
        price=product["price"],
        size=wanted,
        quantity=quantity,
        available=quantity > 0,
        status=stock_status(quantity),
        other_sizes_in_stock=[s.size for s in sizes if s.quantity > 0 and s.size != wanted],
    )


# ---------- chat search that updates the page (Problem 7) ----------

MAX_CARDS = 12


def _to_card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        category=category_for(row["garment_type"]),
        image_file_path=row["image_file_path"],
        image_url="/images/" + Path(row["image_file_path"]).name,
        short_description=short(clean_description(row["description"]), 110),
        in_stock=row["total_quantity"] > 0,
    )


def search_products(ctx: RunContext[ChatDeps], query: str) -> ProductSearchResult:
    """Search the catalogue AND show the matching products as cards on the customer's
    screen. Use this whenever the customer wants to browse or see products, e.g.
    "what hoodies do you have?", "show me your sweatshirts", "any Yale T-shirts?".
    Pass the kind of item plus any details (color, college, sport), e.g. "navy hoodie".
    The cards appear automatically, so don't list every product in your reply."""
    rows, total, unmatched = search_catalogue(ctx.deps.db_path, query, limit=MAX_CARDS)
    # Only show cards that truly match. Partial matches (e.g. "pink" when nothing is
    # pink) are never put on screen as if they were what the customer asked for.
    shown = rows if not unmatched else []
    ctx.deps.searched = True
    ctx.deps.shown_products = [_to_card(r) for r in shown]
    ctx.deps.shown_query = query if shown else None
    ctx.deps.shown_total = total if shown else 0
    ctx.deps.shown_see_all = see_all_path(query) if shown else None

    matches = [_to_match(r) for r in rows]
    if not rows:
        note = "Nothing matched, and no cards are shown. Say so politely and suggest what we do carry."
    elif unmatched:
        note = (
            f"No product matches everything asked for (nothing matched: {', '.join(unmatched)}), so NO cards are "
            "shown. Say clearly we don't carry that; you may mention the closest matches by name."
        )
    elif total > MAX_CARDS:
        note = (
            f"{len(shown)} of {total} matching products are now shown as cards on the page. Briefly introduce "
            f"them and mention they can see all {total} on the Products page."
        )
    else:
        note = f"All {total} matching products are now shown as cards on the page. Briefly introduce them."
    return ProductSearchResult(
        query=query, total_matches=total, matches=matches, unmatched_words=unmatched, note=note
    )


def see_all_path(query: str) -> str:
    return f"/products?q={quote(query)}"


# ---------- filtering by category, size and price (Problem 9) ----------

def filter_catalogue(
    db_path: Path,
    *,
    q: str | None = None,
    category: str | None = None,
    size: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
) -> tuple[list[sqlite3.Row], list[str]]:
    """Products matching every filter given, plus any search words nothing matched.

    Used by both the Products page and the chatbot, so they always agree.
    `size` keeps only products with at least one in stock in that size.
    """
    # A query made only of filler words ("Yale gift ideas") means "anything".
    if q and not [w for w in words(q) if w not in STOP_WORDS]:
        q = None
    if q and q.strip():
        rows, _, unmatched = search_catalogue(db_path, q, limit=10_000)
        if unmatched:
            return [], unmatched
    else:
        with connect(db_path) as conn:
            rows = _catalogue_rows(conn)
    wanted_size = normalize_size(size) if size else None
    out = []
    for r in rows:
        if category and category_for(r["garment_type"]) != category:
            continue
        if wanted_size and wanted_size not in sizes_in_stock(r):
            continue
        if min_price is not None and r["price"] < min_price:
            continue
        if max_price is not None and r["price"] > max_price:
            continue
        out.append(r)
    return out, []


# ---------- recommendations (Problem 9) ----------

MAX_RECOMMENDATIONS = 6


def recommend_products(
    ctx: RunContext[ChatDeps],
    keywords: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
) -> RecommendationResult:
    """Recommend real products that fit what the customer wants, and show them as cards
    on the page. Use for open-ended requests like "a Yale gift under $40", "something warm
    for game day in a large", "a hoodie for my dad under $70".

    keywords: optional style/theme words, e.g. "football", "Berkeley", "navy", "vintage".
    category: optional, one of: T-Shirts, Crewnecks, Hoodies, Quarter-Zips, Jackets & Fleece, Long Sleeves.
    max_price / min_price: budget in dollars, if the customer gave one.
    size: only include products in stock in this size (XS, S, M, L, XL, XXL), if given.
    """
    if category and category not in CATEGORY_NAMES:
        category = next((c for c in CATEGORY_NAMES if c.lower().startswith(category.lower()[:4])), None)
    rows, unmatched = filter_catalogue(
        ctx.deps.db_path, q=keywords, category=category, size=size, min_price=min_price, max_price=max_price
    )
    # If some theme words match nothing in the catalogue (e.g. "game day"), drop just
    # those words and say so, rather than returning nothing at all.
    if keywords and not [w for w in words(keywords) if w not in STOP_WORDS]:
        keywords = None  # only filler words like "Yale gift"
    ignored: list[str] = []

    def in_stock_count(rs: list[sqlite3.Row]) -> int:
        return sum(1 for r in rs if r["total_quantity"] > 0)

    if keywords and (unmatched or not in_stock_count(rows)):
        # Step 1: drop only the words that matched nothing.
        kept = " ".join(w for w in words(keywords) if w not in unmatched and w not in STOP_WORDS) or None
        ignored = list(unmatched)
        rows, unmatched = filter_catalogue(
            ctx.deps.db_path, q=kept, category=category, size=size, min_price=min_price, max_price=max_price
        )
        keywords = kept
        # Step 2: still nothing? Keep the budget, size and category, and drop the theme words.
        if keywords and (unmatched or not in_stock_count(rows)):
            ignored += [w for w in words(keywords) if w not in STOP_WORDS]
            rows, unmatched = filter_catalogue(
                ctx.deps.db_path, category=category, size=size, min_price=min_price, max_price=max_price
            )
            keywords = None
    # Only suggest things someone can actually buy.
    rows = [r for r in rows if r["total_quantity"] > 0]
    # Mix categories and favour items with plenty of stock, so suggestions aren't six of the same tee.
    rows.sort(key=lambda r: (r["price"], -r["total_quantity"], r["name"]))
    picked, seen_names = [], set()
    by_cat: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        by_cat.setdefault(category_for(r["garment_type"]), []).append(r)
    while len(picked) < MAX_RECOMMENDATIONS and any(by_cat.values()):
        for cat in list(by_cat):
            if by_cat[cat] and len(picked) < MAX_RECOMMENDATIONS:
                r = by_cat[cat].pop(0)
                if r["name"] not in seen_names:
                    picked.append(r)
                    seen_names.add(r["name"])

    filters = {k: str(v) for k, v in {
        "keywords": keywords, "category": category, "max_price": max_price, "min_price": min_price,
        "size": normalize_size(size) if size else None,
    }.items() if v not in (None, "")}

    # A friendly title for the results, e.g. "Hoodies under $70 in size L".
    label = " ".join(
        part
        for part in [
            keywords or "",
            category or ("Gifts" if not keywords else ""),
            f"from ${min_price:g}" if min_price is not None else "",
            f"under ${max_price:g}" if max_price is not None else "",
            f"in size {filters['size']}" if "size" in filters else "",
        ]
        if part
    )
    link = {
        "q": keywords or "",
        "category": category or "",
        "size": filters.get("size", ""),
        "min_price": f"{min_price:g}" if min_price is not None else "",
        "max_price": f"{max_price:g}" if max_price is not None else "",
    }
    ctx.deps.searched = True
    ctx.deps.shown_products = [_to_card(r) for r in picked]
    ctx.deps.shown_query = label if picked else None
    ctx.deps.shown_total = len(rows) if picked else 0
    ctx.deps.shown_see_all = ("/products?" + urlencode({k: v for k, v in link.items() if v})) if picked else None

    ignored_note = (
        f" Note: '{', '.join(ignored)}' didn't match anything that fits, so those words were left out "
        "and the other preferences were kept; mention that briefly." if ignored else ""
    )
    if not picked:
        why = f" Nothing matched: {', '.join(unmatched)}." if unmatched else ""
        note = (
            "No in-stock products fit all of these preferences." + why + " Say so kindly and suggest loosening one "
            "thing (a higher budget, another size or category). No cards are shown. Do not invent products."
            + ignored_note
        )
    else:
        note = (
            f"{len(picked)} of {len(rows)} fitting products are now shown as cards. Recommend 2-3 by name with "
            "their price (and sizes if the customer mentioned size). Use only these facts." + ignored_note
        )
    return RecommendationResult(
        filters_used=filters,
        total_matches=len(rows),
        recommendations=[
            Recommendation(
                product_id=r["product_id"],
                name=r["name"],
                category=category_for(r["garment_type"]),
                price=r["price"],
                colors=json.loads(r["colors"]),
                short_description=short(clean_description(r["description"])) or "No description on file yet.",
                sizes_in_stock=sizes_in_stock(r),
            )
            for r in picked
        ],
        note=note,
    )


# ---------- page awareness (Problem 8) ----------

def get_current_page_product(ctx: RunContext[ChatDeps]) -> ProductDetails | NotFound:
    """Get full details (description, colors, price, stock by size) for the product the
    customer is looking at right now. Use this when they say "this", "it", "this one"
    and are on a product page."""
    product_id = ctx.deps.page.product_id if ctx.deps.page else None
    if not product_id:
        return NotFound(error="The customer isn't on a product page right now. Ask which product they mean.")
    return get_product_details(ctx, product_id)


ALL_TOOLS = [
    get_store_info,
    get_website_guide,
    list_product_categories,
    find_products,
    get_product_details,
    check_size_availability,
    search_products,
    get_current_page_product,
    recommend_products,
]
