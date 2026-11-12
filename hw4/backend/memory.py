"""Chat history for logged-in customers (Problem 8).

Messages are stored in the existing `chat_messages` table:

    chat_messages(id, user_id → users.id, role, content, products_json, created_at)

- Only logged-in customers' messages are saved, always under the user id taken
  from their signed session cookie (never from anything typed in the chat).
- Every read is filtered by that same user id, so customers only ever see their
  own conversation.
- Passwords, API keys and similar secrets are blanked out before anything is
  saved or sent to the AI model.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from models import HistoryMessage, ProductCard
from tools import DB_PATH, _to_card

HISTORY_FOR_AGENT = 20   # earlier messages the agent sees for context
HISTORY_FOR_WINDOW = 50  # messages loaded back into the chat window

# Things that look like secrets. They're replaced with [hidden] before saving.
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passcode|passwd|pwd)\b(\s*(is|:|=)\s*|\s+)(\S+)"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),                    # OpenAI-style keys
    re.compile(r"(?i)\b(api[_ -]?key|token|secret)\b(\s*(is|:|=)\s*)(\S+)"),
    re.compile(r"pbkdf2_sha256\$[^\s$]+\$[0-9a-f]{16,}"),         # stored password hashes
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),                        # card-number-like digit runs
]


def redact(text: str) -> str:
    out = text
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 4:
            out = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}[hidden]", out)
        else:
            out = pattern.sub("[hidden]", out)
    return out


def _connect(read_only: bool = False) -> sqlite3.Connection:
    uri = f"file:{DB_PATH}?mode=ro" if read_only else f"file:{DB_PATH}"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema() -> None:
    """The chat_messages table already exists in the course database. Add an index
    so loading one customer's history stays fast. Safe to run repeatedly."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                products_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id, id)")


def save_message(user_id: int, role: str, content: str, products: list[ProductCard] | None = None) -> None:
    if role not in ("user", "assistant"):
        raise ValueError("role must be 'user' or 'assistant'")
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    with _connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, redact(content), products_json),
        )


def _cards_from_json(products_json: str | None) -> list[ProductCard]:
    """Rebuild product cards from saved product ids, using today's catalogue data
    (so prices and images are current, and older saved formats still work)."""
    if not products_json:
        return []
    try:
        ids = [p["product_id"] for p in json.loads(products_json) if isinstance(p, dict) and p.get("product_id")]
    except (ValueError, TypeError):
        return []
    if not ids:
        return []
    with _connect(read_only=True) as conn:
        rows = conn.execute(
            f"""
            SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_quantity
            FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
            WHERE c.product_id IN ({','.join('?' * len(ids))})
            GROUP BY c.product_id
            """,
            ids,
        ).fetchall()
    by_id = {r["product_id"]: r for r in rows}
    return [_to_card(by_id[i]) for i in ids if i in by_id]


def load_history(user_id: int, limit: int = HISTORY_FOR_WINDOW) -> list[HistoryMessage]:
    """The most recent messages for ONE customer, oldest first."""
    with _connect(read_only=True) as conn:
        rows = conn.execute(
            """
            SELECT role, content, products_json, created_at FROM chat_messages
            WHERE user_id = ? AND role IN ('user', 'assistant')
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [
        HistoryMessage(
            role=r["role"],
            content=r["content"],
            products=_cards_from_json(r["products_json"]),
            created_at=r["created_at"],
        )
        for r in reversed(rows)
    ]
