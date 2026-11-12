"""Permanent audit trail for the chatbot (Problem 12).

Every chat interaction is appended to output/audit_trail.json:
when it happened, which tools the assistant used (with short summaries of the
arguments and results), and why the assistant stopped.

Safety:
- Nothing sensitive is written: no passwords, API keys, tokens, session cookies,
  emails, phone numbers or card numbers. Customer text is redacted and shortened.
- New entries are appended. Existing records are never deleted, and they
  survive restarts because they live in a file on disk.
- Writes go to a temporary file first and then replace the original in one
  step, so a crash can't leave half-written JSON behind.
- If the file can't be read (for example someone edited it by hand and broke
  the JSON), it's kept as a backup copy and a fresh file is started. Old
  records are never thrown away.
- Any error while writing is logged and ignored, so the chat keeps working.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from memory import redact

log = logging.getLogger("campus_customs.audit")

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
_LOCK = threading.Lock()

ABOUT = (
    "Campus Customs chatbot audit trail. One entry per chat interaction, oldest first. "
    "Entries are only ever appended. Passwords, API keys, tokens, emails, phone numbers "
    "and card numbers are never recorded."
)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\w)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\w)")


def clean(text: Any, limit: int = 140) -> str:
    """Redact secrets and personal details, collapse whitespace, and shorten."""
    t = redact(str(text if text is not None else ""))
    t = EMAIL.sub("[email hidden]", t)
    t = PHONE.sub("[phone hidden]", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= limit else t[: limit - 1].rstrip() + "…"


# ---------- short summaries of tool arguments and results ----------

def summarize_args(args: dict[str, Any] | None) -> str:
    if not args:
        return "(none)"
    return clean(", ".join(f"{k}={v!r}" for k, v in args.items()), 160)


def summarize_result(content: Any) -> str:
    """Turn a tool's structured result into one readable line."""
    try:
        if hasattr(content, "model_dump"):
            data = content.model_dump()
        elif isinstance(content, list):
            data = [c.model_dump() if hasattr(c, "model_dump") else c for c in content]
        else:
            data = content

        if isinstance(data, dict):
            if "error" in data and len(data) == 1:
                return clean(f"not found: {data['error']}")
            if "matches" in data:  # ProductSearchResult
                names = ", ".join(f"{m['name']} (${m['price']:.2f})" for m in data["matches"][:3])
                extra = f"; unmatched words: {data['unmatched_words']}" if data.get("unmatched_words") else ""
                return clean(f"{data['total_matches']} match(es): {names or 'none'}{extra}", 200)
            if "recommendations" in data:  # RecommendationResult
                names = ", ".join(f"{r['name']} (${r['price']:.2f})" for r in data["recommendations"][:3])
                return clean(f"{data['total_matches']} fitting product(s); suggested: {names or 'none'}", 200)
            if "quantity" in data and "size" in data:  # InventoryResult
                return clean(
                    f"{data['product_name']} size {data['size']}: {data['quantity']} ({data['status']}), "
                    f"${data['price']:.2f}"
                )
            if "sizes" in data and "price" in data:  # ProductDetails
                return clean(
                    f"{data['name']}: ${data['price']:.2f}, {data['total_quantity']} in stock, "
                    f"sizes in stock {data.get('sizes_in_stock')}"
                )
            if "address" in data:  # StoreInfo
                return "store details (name, address, website, what we sell, unknown topics)"
        if isinstance(data, list):
            return clean(f"{len(data)} item(s)" + (f", e.g. {data[0]}" if data else ""), 160)
        return clean(data, 160)
    except Exception:  # never let a summary break the chat
        return clean(content, 160)


# ---------- reading and appending ----------

def _empty() -> dict[str, Any]:
    return {"about": ABOUT, "format_version": 1, "entries": []}


def _load() -> dict[str, Any]:
    if not AUDIT_PATH.exists():
        return _empty()
    try:
        data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data
        if isinstance(data, list):  # tolerate a plain list of entries
            return {**_empty(), "entries": data}
        raise ValueError("unexpected structure")
    except Exception as exc:
        # Keep the unreadable file instead of overwriting it, then start fresh.
        backup = AUDIT_PATH.with_name(f"audit_trail.unreadable-{datetime.now():%Y%m%d-%H%M%S}.json")
        try:
            AUDIT_PATH.replace(backup)
            log.warning("Audit file couldn't be read (%s); kept it as %s and started a new one.", exc, backup.name)
        except OSError:
            log.warning("Audit file couldn't be read or moved (%s).", exc)
        return _empty()


def _write(data: dict[str, Any]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".audit-", suffix=".json", dir=AUDIT_PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, AUDIT_PATH)  # one-step swap: the file is never half-written
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def record(
    *,
    answered_by: str,
    stop_reason: str,
    tool_calls: list[dict[str, str]],
    question: str,
    reply: str,
    logged_in: bool,
    page_path: str | None,
    duration_seconds: float,
    model_requests: int = 0,
) -> None:
    """Append one interaction to the audit trail. Never raises."""
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "interaction_id": uuid.uuid4().hex[:12],
        "visitor": "logged-in customer" if logged_in else "guest",
        "page": clean(page_path or "/", 80),
        "question_preview": clean(question, 120),
        "answered_by": answered_by,
        "tool_calls": tool_calls or [],
        "tools_used": [t["tool"] for t in tool_calls] or ["(none)"],
        "stop_reason": stop_reason,
        "model_requests": model_requests,
        "duration_seconds": round(duration_seconds, 2),
        "reply_preview": clean(reply, 160),
    }
    try:
        with _LOCK:
            data = _load()
            data["entries"].append(entry)
            _write(data)
    except Exception as exc:
        log.error("Couldn't write to the audit trail (%s: %s). The chat continues.", type(exc).__name__, exc)


def ensure_file() -> None:
    """Create an empty, valid audit file on first start (keeps existing records)."""
    try:
        with _LOCK:
            if not AUDIT_PATH.exists():
                _write(_empty())
    except Exception as exc:
        log.error("Couldn't create the audit trail file (%s).", exc)
