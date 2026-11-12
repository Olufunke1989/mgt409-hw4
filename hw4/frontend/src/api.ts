import type { ChatMessage, ChatProductCard, PageContext, Product, ProductDetail } from "./types";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(res.status === 404 ? "not-found" : `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export interface ProductFilters {
  q?: string;
  category?: string;
  size?: string;
  min_price?: string;
  max_price?: string;
}

export function fetchProducts(params: ProductFilters = {}) {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v) search.set(k, v);
  const qs = search.toString();
  return getJson<Product[]>(`/api/products${qs ? `?${qs}` : ""}`);
}

export function fetchProduct(productId: string) {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`);
}

export function fetchSizes() {
  return getJson<string[]>("/api/sizes");
}

export function fetchCategories() {
  return getJson<string[]>("/api/categories");
}

export type ChatResult =
  | {
      status: "ok";
      reply: string;
      answeredBy: "ai" | "database" | "fallback";
      searched: boolean;
      products: ChatProductCard[];
      searchQuery: string | null;
      totalMatches: number;
      seeAllPath: string | null;
    }
  | { status: "error"; message: string };

/** Sends the conversation to the FastAPI chat endpoint, which runs the PydanticAI agent. */
export async function sendChatMessage(history: ChatMessage[], page: PageContext): Promise<ChatResult> {
  // Give up after 60 seconds so the chat never hangs forever.
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 60_000);
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history, page }),
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = typeof data?.detail === "string" ? data.detail : "";
      return {
        status: "error",
        message: res.status >= 500 || !detail ? "Sorry, I had trouble answering just now. Please try again in a moment." : detail,
      };
    }
    return {
      status: "ok",
      reply: data.reply,
      answeredBy: data.answered_by ?? "ai",
      searched: Boolean(data.searched),
      products: data.products ?? [],
      searchQuery: data.search_query ?? null,
      totalMatches: data.total_matches ?? 0,
      seeAllPath: data.see_all_path ?? null,
    };
  } catch (err) {
    const timedOut = err instanceof DOMException && err.name === "AbortError";
    return {
      status: "error",
      message: timedOut
        ? "Sorry, that took too long. Please try again."
        : "I couldn't reach the shop. Please check your internet connection and try again.",
    };
  } finally {
    window.clearTimeout(timer);
  }
}

/** The logged-in customer's saved conversation (empty for guests). */
export async function fetchChatHistory(): Promise<ChatMessage[]> {
  const res = await fetch("/api/chat/history", { credentials: "include" });
  if (!res.ok) return [];
  const data = (await res.json()) as { messages: { role: "user" | "assistant"; content: string; products: ChatProductCard[] }[] };
  return data.messages.map((m) => ({ role: m.role, content: m.content, products: m.products }));
}

export const formatPrice = (price: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(price);
