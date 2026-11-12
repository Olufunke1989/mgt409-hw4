"""Pydantic models for the chat API and the chatbot's tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ---------- chat API ----------

class ChatMessage(BaseModel):
    """One message in the conversation, as sent by the website."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class PageContext(BaseModel):
    """Which page the customer is looking at when they send a message (Problem 8)."""

    path: str = Field("/", max_length=200)
    product_id: str | None = Field(None, max_length=120, description="Set when on a product page.")


class ChatRequest(BaseModel):
    """The conversation so far. The last message is the customer's new one.

    For logged-in customers the server uses their saved history instead of the
    earlier messages sent here, so only the last message matters."""

    messages: list[ChatMessage] = Field(min_length=1, max_length=50)
    page: PageContext | None = None


class ProductCard(BaseModel):
    """A product the website should show as a card (Problem 7)."""

    product_id: str
    name: str
    price: float
    category: str
    image_file_path: str = Field(description="Path stored in the catalogue, relative to data/.")
    image_url: str = Field(description="Where the website loads the image from.")
    short_description: str
    in_stock: bool


class ChatResponse(BaseModel):
    """What the website gets back: the written reply plus any products to show."""

    reply: str
    answered_by: Literal["ai", "database", "fallback"] = Field(
        "ai", description="ai = the agent, database = instant lookup, fallback = AI was unavailable."
    )
    searched: bool = Field(False, description="True when the assistant ran a catalogue search this turn.")
    products: list[ProductCard] = Field(default_factory=list)
    search_query: str | None = Field(None, description="What was searched, when products are shown.")
    total_matches: int = 0
    see_all_path: str | None = Field(None, description="Products-page link with every match.")


class CustomerInfo(BaseModel):
    """The logged-in customer, taken from their session. Never includes the password hash."""

    first_name: str
    last_name: str
    email: str


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    products: list["ProductCard"] = Field(default_factory=list)
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[HistoryMessage]


# ---------- tool results ----------

class StoreInfo(BaseModel):
    """Verified facts about Campus Customs. Anything not here is unknown."""

    name: str
    address: str
    online_store: str
    what_we_sell: str
    unknown_topics: list[str] = Field(
        description="Things we have no verified information about, so the assistant must not guess."
    )


class SitePage(BaseModel):
    name: str
    path: str
    what_it_is_for: str


class CategorySummary(BaseModel):
    category: str
    product_count: int


# ---------- product and inventory results (Problem 6) ----------
# Field names follow the real database columns:
#   catalogue(product_id, name, garment_type, description, colors, search_tags, image_file_path, price)
#   inventory(id, product_id, size, quantity)

StockStatus = Literal["in stock", "low stock", "sold out"]


class ProductMatch(BaseModel):
    """A short summary of one product that matched a search."""

    product_id: str
    name: str
    garment_type: str
    category: str
    price: float
    colors: list[str]
    short_description: str
    total_quantity: int = Field(description="Units in stock across all sizes.")
    in_stock: bool


class ProductSearchResult(BaseModel):
    """Result of looking up products by a customer's description."""

    query: str
    total_matches: int
    matches: list[ProductMatch]
    unmatched_words: list[str] = Field(
        default_factory=list, description="Search words no returned product matched (e.g. a color we don't carry)."
    )
    note: str = Field(description="Guidance for the assistant on how to use these results.")


class SizeAvailability(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class ProductDetails(BaseModel):
    """Everything the store knows about one product, including stock for each size."""

    product_id: str
    name: str
    garment_type: str
    category: str
    description: str
    colors: list[str]
    price: float
    total_quantity: int
    in_stock: bool
    sizes: list[SizeAvailability]
    sizes_in_stock: list[str]
    page_path: str = Field(description="Link to this product's page on the website.")


class InventoryResult(BaseModel):
    """Stock for one product in one size."""

    product_id: str
    product_name: str
    price: float
    size: str
    quantity: int
    available: bool
    status: StockStatus
    other_sizes_in_stock: list[str]


class NotFound(BaseModel):
    """Returned instead of a result when something can't be found."""

    error: str


HistoryMessage.model_rebuild()


# ---------- recommendations (Problem 9) ----------

class Recommendation(BaseModel):
    """One real product suggested to the customer, with live price and sizes."""

    product_id: str
    name: str
    category: str
    price: float
    colors: list[str]
    short_description: str
    sizes_in_stock: list[str]


class RecommendationResult(BaseModel):
    """What recommend_products found. Everything here comes from the database."""

    filters_used: dict[str, str]
    total_matches: int
    recommendations: list[Recommendation]
    note: str
