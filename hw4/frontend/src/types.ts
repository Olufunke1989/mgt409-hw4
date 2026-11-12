export interface Product {
  product_id: string;
  name: string;
  garment_type: string;
  category: string;
  description: string;
  colors: string[];
  price: number;
  image_url: string;
  total_stock: number;
}

export interface SizeStock {
  size: string;
  quantity: number;
}

export interface ProductDetail extends Product {
  search_tags: string[];
  sizes: SizeStock[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  /** True for local error notes that shouldn't be sent back to the agent. */
  error?: boolean;
  /** Products the assistant showed with this reply (Problem 7/8). */
  products?: ChatProductCard[];
  /** "database" = instant lookup, "fallback" = AI was unavailable (Problem 9). */
  answeredBy?: "ai" | "database" | "fallback";
  /** For error notes: the customer message to resend with "Try again". */
  retryText?: string;
}

/** Where the customer is when they send a message (Problem 8). */
export interface PageContext {
  path: string;
  product_id: string | null;
}

/** A product the chatbot found, shown as a card on the page (Problem 7). */
export interface ChatProductCard {
  product_id: string;
  name: string;
  price: number;
  category: string;
  image_file_path: string;
  image_url: string;
  short_description: string;
  in_stock: boolean;
}

export interface ChatSearchResults {
  query: string;
  total: number;
  products: ChatProductCard[];
  seeAllPath: string | null;
}
