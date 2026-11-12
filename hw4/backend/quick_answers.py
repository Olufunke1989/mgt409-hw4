"""Instant answers for very simple questions, straight from the database (Problem 9).

Some chat messages don't need the AI at all, for example "What hoodies do you
have?" or "How much is this?" on a product page. Answering those with a plain
database lookup is faster, cheaper, and works even if the AI service is down.

The patterns are deliberately strict: anything with extra details (a budget,
a color, a size, "for my dad"…) goes to the AI agent instead.
"""

from __future__ import annotations

import re

from tools import (
    MAX_CARDS,
    ChatDeps,
    _to_card,
    category_for,
    connect,
    filter_catalogue,
    sizes_in_stock,
)

# Customer words → the website's categories.
CATEGORY_WORDS = {
    "hoodies": "Hoodies", "hoodie": "Hoodies", "hooded sweatshirts": "Hoodies",
    "crewnecks": "Crewnecks", "crewneck": "Crewnecks", "crewneck sweatshirts": "Crewnecks",
    "t-shirts": "T-Shirts", "t shirts": "T-Shirts", "tshirts": "T-Shirts", "tees": "T-Shirts", "shirts": "T-Shirts",
    "quarter zips": "Quarter-Zips", "quarter-zips": "Quarter-Zips", "1/4 zips": "Quarter-Zips", "quarterzips": "Quarter-Zips",
    "jackets": "Jackets & Fleece", "fleece": "Jackets & Fleece", "fleeces": "Jackets & Fleece",
    "long sleeves": "Long Sleeves", "long-sleeves": "Long Sleeves", "long sleeve shirts": "Long Sleeves",
}
_CAT = "|".join(sorted(map(re.escape, CATEGORY_WORDS), key=len, reverse=True))

BROWSE = re.compile(
    rf"^(?:hi[,!.]?\s+)?(?:(?:can you |could you |please )?show me(?: all)?(?: of)?(?: your| the)?"
    rf"|what(?: kind of| kinds of| types of)?(?: yale)? (?:{_CAT}) do you (?:have|sell|carry)"
    rf"|do you (?:have|sell|carry)(?: any)?(?: yale)?"
    rf"|(?:i'?d like to |i want to |let me )?(?:see|browse)(?: your| the| all)?)"
    rf"\s*(?:yale\s+)?(?P<cat>{_CAT})?(?:\s+please)?\s*[?.!]*$",
    re.IGNORECASE,
)
PRICE_OF_THIS = re.compile(
    r"^(?:how much (?:is|does) (?:this|it)(?: one)?(?: cost)?|what(?:'s| is) the price(?: of this| of it)?|price\??)\s*[?.!]*$",
    re.IGNORECASE,
)


def _category_from(text: str) -> str | None:
    m = BROWSE.match(text.strip())
    if not m:
        return None
    word = m.group("cat")
    if not word:
        # "What hoodies do you have?" puts the category in the middle.
        inner = re.search(rf"\b({_CAT})\b", text, re.IGNORECASE)
        word = inner.group(1) if inner else None
    return CATEGORY_WORDS.get(word.lower()) if word else None


def try_quick_answer(text: str, deps: ChatDeps) -> str | None:
    """Return a reply if this message can be answered from the database alone."""
    category = _category_from(text)
    if category:
        rows, _ = filter_catalogue(deps.db_path, category=category)
        rows.sort(key=lambda r: r["name"])
        shown = rows[:MAX_CARDS]
        deps.searched = True
        deps.shown_products = [_to_card(r) for r in shown]
        deps.shown_query = category
        deps.shown_total = len(rows)
        deps.shown_see_all = f"/products?category={category.replace('&', '%26').replace(' ', '%20')}"
        prices = sorted({r["price"] for r in rows})
        price_text = f"all priced at ${prices[0]:.2f}" if len(prices) == 1 else f"priced from ${prices[0]:.2f} to ${prices[-1]:.2f}"
        more = f" I've put {len(shown)} of them on the page, and you can see all {len(rows)} on Products (/products)." if len(rows) > len(shown) else " They're all on the page for you now."
        name = f", {deps.customer.first_name}" if deps.customer else ""
        return (
            f"Sure thing{name}! We have {len(rows)} {category.lower()}, {price_text}.{more} "
            "Let me know if you'd like help with a size, color or budget."
        )

    page_product = deps.page.product_id if deps.page else None
    if page_product and PRICE_OF_THIS.match(text.strip()):
        with connect(deps.db_path) as conn:
            row = conn.execute(
                """
                SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_quantity,
                       COALESCE(GROUP_CONCAT(CASE WHEN i.quantity > 0 THEN i.size END), '') AS sizes_in_stock
                FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
                WHERE c.product_id = ? GROUP BY c.product_id
                """,
                (page_product,),
            ).fetchone()
        if row is None:
            return None
        in_stock = sizes_in_stock(row)
        stock_text = (
            f"It's in stock in {', '.join(in_stock)}." if in_stock else "Unfortunately it's sold out in every size right now."
        )
        return f"The {row['name']} is ${row['price']:.2f}. {stock_text}"

    return None


__all__ = ["try_quick_answer", "category_for"]
