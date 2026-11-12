import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct, formatPrice } from "../api";
import { swatchFor, tintFor } from "../design";
import type { ProductDetail } from "../types";

const LOW_STOCK = 3;

export default function ProductPage() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState<"" | "not-found" | "failed">("");
  const [size, setSize] = useState<string>("");
  const [notice, setNotice] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    setProduct(null);
    setError("");
    setSize("");
    setNotice("");
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) => setError(e.message === "not-found" ? "not-found" : "failed"));
  }, [productId, reloadKey]);

  if (error) {
    return (
      <div className="container page empty">
        <h1>{error === "not-found" ? "We couldn't find that product" : "Something went wrong"}</h1>
        <p className="muted">
          {error === "not-found"
            ? "It may have been removed or the link might be wrong."
            : "We couldn't load this product. Please make sure the shop server is running."}
        </p>
        <div className="empty-actions">
          {error === "failed" && (
            <button className="btn btn-ghost" onClick={() => setReloadKey((k) => k + 1)}>Try again</button>
          )}
          <Link to="/products" className="btn btn-primary">Back to products</Link>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container page">
        <p className="loading-text" role="status">Loading product details…</p>
        <div className="detail-grid">
          <div className="skeleton-block" />
          <div className="skeleton-block short" />
        </div>
      </div>
    );
  }

  const selected = product.sizes.find((s) => s.size === size);
  const soldOut = product.total_stock === 0;

  return (
    <div className="container page">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <Link to="/">Home</Link> / <Link to="/products">Products</Link> /{" "}
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>{product.category}</Link>
      </nav>

      <div className="detail-grid">
        <div className={`detail-image ${tintFor(product.product_id)}`}>
          <div className="photo">
            <img src={product.image_url} alt={product.name} />
          </div>
        </div>

        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price price-lg">{formatPrice(product.price)}</p>
          <p className="detail-desc">
            {product.description || "A full description for this item is coming soon. Stop by the shop to see it in person!"}
          </p>

          {product.colors.length > 0 && (
            <div className="detail-section">
              <h2>Colors</h2>
              <ul className="color-list">
                {product.colors.map((c) => (
                  <li key={c}>
                    <i style={{ "--swatch": swatchFor(c) } as React.CSSProperties} aria-hidden="true" />
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="detail-section">
            <div className="size-head">
              <h2>Size</h2>
              {selected && (
                <span className={`stock-note ${selected.quantity <= LOW_STOCK ? "low" : ""}`}>
                  {selected.quantity <= LOW_STOCK ? `Only ${selected.quantity} left` : `${selected.quantity} in stock`}
                </span>
              )}
            </div>
            {soldOut && <p className="notice">This item is currently sold out in every size.</p>}
            <div className="sizes" role="radiogroup" aria-label="Choose a size">
              {product.sizes.map((s) => {
                const out = s.quantity === 0;
                return (
                  <button
                    key={s.size}
                    role="radio"
                    aria-checked={size === s.size}
                    className={`size ${size === s.size ? "active" : ""} ${out ? "out" : ""}`}
                    disabled={out}
                    title={out ? `${s.size} is sold out` : `${s.quantity} in stock`}
                    onClick={() => {
                      setSize(s.size);
                      setNotice("");
                    }}
                  >
                    {s.size}
                  </button>
                );
              })}
            </div>

            <table className="stock-table">
              <caption className="sr-only">Stock by size</caption>
              <thead>
                <tr><th scope="col">Size</th><th scope="col">Availability</th></tr>
              </thead>
              <tbody>
                {product.sizes.map((s) => (
                  <tr key={s.size}>
                    <td>{s.size}</td>
                    <td className={s.quantity === 0 ? "out" : s.quantity <= LOW_STOCK ? "low" : "ok"}>
                      {s.quantity === 0 ? "Sold out" : `${s.quantity} in stock`}
                      {s.quantity > 0 && (
                        <span className="stock-bar" aria-hidden="true">
                          <i style={{ width: `${Math.min(100, (s.quantity / 25) * 100)}%` }} />
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            className="btn btn-primary btn-lg btn-block"
            disabled={soldOut || !size}
            onClick={() =>
              setNotice(
                `Online checkout is coming soon. In the meantime, size ${size} is available at our shop at 57 Broadway.`,
              )
            }
          >
            {soldOut ? "Sold out" : size ? `Add size ${size} to bag` : "Choose a size"}
          </button>
          {notice && <p className="notice" role="status">{notice}</p>}

          <div className="perk-row">
            <div><strong>Officially licensed</strong>Genuine Yale marks</div>
            <div><strong>Try it on</strong>At 57 Broadway, New Haven</div>
            <div><strong>Questions?</strong>Ask our assistant below</div>
          </div>

          <Link to="/products" className="text-link back-link">← Keep shopping</Link>
        </div>
      </div>
    </div>
  );
}
