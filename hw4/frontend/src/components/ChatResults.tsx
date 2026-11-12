import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useChatResults } from "../chatResults";
import type { Product } from "../types";
import ProductCard from "./ProductCard";

/** Shows the products the chatbot found, using the same cards as the Products page. */
export default function ChatResults() {
  const { results, open, setOpen, setResults } = useChatResults();
  const ref = useRef<HTMLElement>(null);

  // Bring new results into view as soon as they arrive.
  useEffect(() => {
    if (results && open) ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [results, open]);

  if (!results) return null;

  if (!open) {
    return (
      <div className="container chat-results-collapsed">
        <button className="chip active" onClick={() => setOpen(true)}>
          Show chat results for “{results.query}” ({results.products.length})
        </button>
      </div>
    );
  }

  return (
    <section ref={ref} className="chat-results container" aria-live="polite" aria-label="Products from your chat">
      <div className="section-head">
        <div>
          <p className="eyebrow">From your chat</p>
          <h2>
            Results for “{results.query}”
          </h2>
          <p className="muted result-count">
            Showing {results.products.length} of {results.total} matching{" "}
            {results.total === 1 ? "product" : "products"}
          </p>
        </div>
        <div className="chat-results-actions">
          {results.seeAllPath && results.total > results.products.length && (
            <Link to={results.seeAllPath} className="btn btn-ghost">
              See all {results.total}
            </Link>
          )}
          <button className="icon-btn" aria-label="Hide chat results" onClick={() => setOpen(false)}>
            ✕
          </button>
          <button className="text-link clear-btn" onClick={() => setResults(null)}>
            Clear
          </button>
        </div>
      </div>
      <div className="grid" onClick={(e) => (e.target as HTMLElement).closest("a") && setOpen(false)}>
        {results.products.map((p) => (
          <ProductCard
            key={p.product_id}
            product={{
              ...p,
              description: p.short_description,
              garment_type: p.category,
              colors: [],
              total_stock: p.in_stock ? 1 : 0,
            } satisfies Product}
          />
        ))}
      </div>
    </section>
  );
}
