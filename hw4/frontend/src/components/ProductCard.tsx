import { Link } from "react-router-dom";
import { formatPrice } from "../api";
import { tintFor } from "../design";
import type { Product } from "../types";

export default function ProductCard({ product }: { product: Product }) {
  const soldOut = product.total_stock === 0;
  return (
    <Link to={`/products/${product.product_id}`} className={`product-card ${tintFor(product.product_id)}`}>
      <div className="product-card-image">
        <div className="photo">
          <img src={product.image_url} alt={product.name} loading="lazy" />
        </div>
        {soldOut && <span className="badge badge-muted">Sold out</span>}
        <span className="view-pill" aria-hidden="true">View details →</span>
      </div>
      <div className="product-card-body">
        <p className="eyebrow">{product.category}</p>
        <h3>{product.name}</h3>
        <p className="product-card-desc">{product.description || "Description coming soon."}</p>
        <p className="price">{formatPrice(product.price)}</p>
      </div>
    </Link>
  );
}
