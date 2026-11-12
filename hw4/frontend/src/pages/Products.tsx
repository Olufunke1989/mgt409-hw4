import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchCategories, fetchProducts, fetchSizes, formatPrice } from "../api";
import ProductCard from "../components/ProductCard";
import type { Product } from "../types";

type Sort = "name" | "price-asc" | "price-desc";

// Price bands that fit this catalogue ($32–$98).
const PRICE_BANDS = [
  { id: "", label: "Any price", min: "", max: "" },
  { id: "under-40", label: "Under $40", min: "", max: "39.99" },
  { id: "40-60", label: "$40 – $60", min: "40", max: "60" },
  { id: "60-80", label: "$60 – $80", min: "60.01", max: "80" },
  { id: "80-plus", label: "$80 & up", min: "80.01", max: "" },
];

function priceSpan(prices: number[]) {
  const lo = Math.min(...prices);
  const hi = Math.max(...prices);
  return lo === hi ? `all ${formatPrice(lo)}` : `${formatPrice(lo)}–${formatPrice(hi)}`;
}

export default function Products() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const category = params.get("category") ?? "";
  const size = params.get("size") ?? "";
  const priceId = params.get("price") ?? "";
  const sort = (params.get("sort") as Sort) || "name";
  // A custom range can also arrive in the link (e.g. from the chatbot: ?max_price=40).
  const customMin = params.get("min_price") ?? "";
  const customMax = params.get("max_price") ?? "";
  const band =
    PRICE_BANDS.find((b) => b.id === priceId && b.id) ??
    (customMin || customMax
      ? {
          id: "custom",
          label: customMin && customMax ? `$${customMin} – $${customMax}` : customMax ? `Up to $${customMax}` : `$${customMin} & up`,
          min: customMin,
          max: customMax,
        }
      : PRICE_BANDS[0]);

  const [draft, setDraft] = useState(q);
  const [categories, setCategories] = useState<string[]>([]);
  const [sizes, setSizes] = useState<string[]>([]);
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [filtersOpen, setFiltersOpen] = useState(false);

  useEffect(() => {
    setDraft(q);
  }, [q]);

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]));
    fetchSizes().then(setSizes).catch(() => setSizes([]));
  }, []);

  // Typing in the search box updates results automatically after a short pause.
  useEffect(() => {
    if (draft.trim() === (new URLSearchParams(window.location.search).get("q") ?? "")) return;
    const t = window.setTimeout(() => update({ q: draft.trim() }), 350);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft]);

  useEffect(() => {
    let cancelled = false;
    setProducts(null);
    setError(false);
    fetchProducts({ q, category, size, min_price: band.min, max_price: band.max })
      .then((p) => !cancelled && setProducts(p))
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, [q, category, size, band.min, band.max, reloadKey]);

  const sorted = useMemo(() => {
    if (!products) return null;
    const list = [...products];
    if (sort === "price-asc") list.sort((a, b) => a.price - b.price);
    if (sort === "price-desc") list.sort((a, b) => b.price - a.price);
    return list;
  }, [products, sort]);

  // Always start from the address bar's current filters (not an older copy),
  // so a delayed search-box update can't bring back filters that were just cleared.
  function update(next: Record<string, string>) {
    setParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        for (const [k, v] of Object.entries(next)) {
          if (v) p.set(k, v);
          else p.delete(k);
        }
        return p;
      },
      { replace: "q" in next },
    );
  }

  const active: { key: string; label: string }[] = [
    ...(q ? [{ key: "q", label: `“${q}”` }] : []),
    ...(category ? [{ key: "category", label: category }] : []),
    ...(size ? [{ key: "size", label: `Size ${size}` }] : []),
    ...(band.id ? [{ key: "price", label: band.label }] : []),
  ];
  const filterCount = active.filter((a) => a.key !== "q").length;
  const clearAll = () => {
    setDraft("");
    setParams({});
  };

  return (
    <div className="container page">
      <header className="page-banner">
        <span className="blob blob-butter float-slow" style={{ width: 160, height: 160, right: "8%", top: -50 }} aria-hidden="true" />
        <span className="blob blob-coral float-slower" style={{ width: 70, height: 70, right: "22%", bottom: -25 }} aria-hidden="true" />
        <span className="blob blob-electric" style={{ width: 26, height: 26, right: "4%", bottom: "22%" }} aria-hidden="true" />
        <p className="eyebrow">The full collection</p>
        <h1>
          Shop <em>Yale</em> apparel
        </h1>
        <p className="muted">Search by name or keyword, then narrow things down by category, size or price.</p>
      </header>

      {filtersOpen && <div className="sheet-backdrop" onClick={() => setFiltersOpen(false)} aria-hidden="true" />}
      <div className="shop-layout">
        <aside className={`filters ${filtersOpen ? "open" : ""}`} aria-label="Filters" id="filters-panel">
          <div className="filters-head">
            <h2>Filters</h2>
            {(filterCount > 0 || q) && (
              <button className="text-link clear-btn" onClick={clearAll}>Clear all</button>
            )}
          </div>

          <fieldset className="filter-group">
            <legend>Category</legend>
            <div className="chips">
              <button className={`chip ${!category ? "active" : ""}`} aria-pressed={!category} onClick={() => update({ category: "" })}>
                All
              </button>
              {categories.map((c) => (
                <button key={c} className={`chip ${category === c ? "active" : ""}`} aria-pressed={category === c} onClick={() => update({ category: category === c ? "" : c })}>
                  {c}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="filter-group">
            <legend>Size in stock</legend>
            <div className="size-filter">
              {sizes.map((sz) => (
                <button key={sz} className={`size ${size === sz ? "active" : ""}`} aria-pressed={size === sz} onClick={() => update({ size: size === sz ? "" : sz })}>
                  {sz}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset className="filter-group">
            <legend>Price</legend>
            <div className="price-options" role="radiogroup" aria-label="Price range">
              {PRICE_BANDS.map((b) => (
                <label key={b.id || "any"} className={`price-option ${band.id === b.id ? "active" : ""}`}>
                  <input type="radio" name="price" checked={band.id === b.id} onChange={() => update({ price: b.id, min_price: "", max_price: "" })} />
                  {b.label}
                </label>
              ))}
            </div>
          </fieldset>

          <button className="btn btn-primary btn-block filters-done" onClick={() => setFiltersOpen(false)}>
            Show {sorted ? sorted.length : ""} results
          </button>
        </aside>

        <section className="shop-results">
          <div className="toolbar">
            <form
              className="search"
              role="search"
              onSubmit={(e) => {
                e.preventDefault();
                update({ q: draft.trim() });
              }}
            >
              <label htmlFor="search" className="sr-only">Search products</label>
              <input id="search" type="search" placeholder="Search hoodies, colleges, sports, colors…" value={draft} onChange={(e) => setDraft(e.target.value)} />
              <button className="btn btn-primary" type="submit">Search</button>
            </form>
            <div className="toolbar-right">
              <button className="btn btn-ghost filters-toggle" aria-expanded={filtersOpen} aria-controls="filters-panel" onClick={() => setFiltersOpen((o) => !o)}>
                Filters{filterCount ? ` (${filterCount})` : ""}
              </button>
              <label className="sort">
                <span>Sort by</span>
                <select value={sort} onChange={(e) => update({ sort: e.target.value === "name" ? "" : e.target.value })}>
                  <option value="name">Name (A–Z)</option>
                  <option value="price-asc">Price: low to high</option>
                  <option value="price-desc">Price: high to low</option>
                </select>
              </label>
            </div>
          </div>

          {active.length > 0 && (
            <div className="active-filters" aria-label="Active filters">
              {active.map((a) => (
                <button key={a.key} className="chip active removable" onClick={() => (a.key === "q" ? (setDraft(""), update({ q: "" })) : a.key === "price" ? update({ price: "", min_price: "", max_price: "" }) : update({ [a.key]: "" }))} aria-label={`Remove filter ${a.label}`}>
                  {a.label} <span aria-hidden="true">✕</span>
                </button>
              ))}
            </div>
          )}

          {error ? (
            <div className="notice notice-error state-box" role="alert">
              <strong>We couldn't load products right now.</strong>
              <p>Please check that the shop server is running, then try again.</p>
              <button className="btn btn-ghost" onClick={() => setReloadKey((k) => k + 1)}>Try again</button>
            </div>
          ) : !sorted ? (
            <>
              <p className="result-count loading-text" role="status">Loading products…</p>
              <div className="grid">{Array.from({ length: 6 }, (_, i) => <div key={i} className="skeleton-card" />)}</div>
            </>
          ) : sorted.length === 0 ? (
            <div className="empty state-box" role="status">
              <p className="empty-icon" aria-hidden="true">🔍</p>
              <h2>No products match {q ? `“${q}”` : "these filters"}{active.some((a) => a.key !== "q") ? " with these filters" : ""}.</h2>
              <p className="muted">
                Try a different word (like “hoodie”, “Berkeley” or “navy”), remove a filter, or ask our assistant in the
                corner for ideas.
              </p>
              <div className="empty-actions">
                {filterCount > 0 && <button className="btn btn-ghost" onClick={() => update({ category: "", size: "", price: "", min_price: "", max_price: "" })}>Remove filters</button>}
                <button className="btn btn-primary" onClick={clearAll}>See all products</button>
              </div>
            </div>
          ) : (
            <>
              <p className="result-count" role="status">
                {sorted.length} {sorted.length === 1 ? "product" : "products"}
                {band.id && sorted.length > 0 && ` · ${priceSpan(sorted.map((p) => p.price))}`}
              </p>
              <div className="grid">
                {sorted.map((p, i) => (
                  <div key={p.product_id} className="reveal" style={{ "--delay": `${(i % 3) * 0.06}s` } as React.CSSProperties}>
                    <ProductCard product={p} />
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
