import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { fetchProducts, formatPrice } from "../api";
import { useAuth } from "../auth";
import ProductCard from "../components/ProductCard";
import type { Product } from "../types";

// Real catalogue items used in the hero "lookbook" collage.
const HERO_IDS = ["basic-hoodie-big-yale", "2025-yale-vs-harvard-t-shirt", "benjamin-franklin-1-4-zip"];
const FEATURED_IDS = [
  "champion-reverse-weave-hoodie-1",
  "brooks-brothers-bomber-jacket-yale",
  "davenport-college-crewneck",
  "berkeley-1-4-zip",
];
const MARQUEE = ["Hoodies", "Crewnecks", "Game day tees", "Residential colleges", "Quarter-zips", "Varsity sports", "New Haven made"];
const CATEGORY_BLURBS: Record<string, string> = {
  Hoodies: "Cozy layers",
  Crewnecks: "Everyday classics",
  "T-Shirts": "Game day ready",
  "Quarter-Zips": "Polished & warm",
  "Jackets & Fleece": "Bundle up",
  "Long Sleeves": "Light layers",
};

function stagger(i: number) {
  return { "--delay": `${(i % 4) * 0.08}s` } as React.CSSProperties;
}

export default function Home() {
  const { user } = useAuth();
  const location = useLocation();
  const welcome = Boolean((location.state as { welcome?: boolean } | null)?.welcome) && user;
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => setError(true));
  }, []);

  const byId = useMemo(() => new Map(products.map((p) => [p.product_id, p])), [products]);
  const hero = HERO_IDS.map((id) => byId.get(id)).filter((p): p is Product => Boolean(p));

  const featured = useMemo(() => {
    const picked = FEATURED_IDS.map((id) => byId.get(id)).filter((p): p is Product => Boolean(p));
    return picked.length === 4 ? picked : products.slice(0, 4);
  }, [byId, products]);

  // "Fresh picks": one standout per category (the best-stocked style), chosen from the
  // live catalogue. Not "new arrivals", because the catalogue doesn't record arrival dates.
  const fresh = useMemo(() => {
    const skip = new Set([...FEATURED_IDS, ...HERO_IDS]);
    const best = new Map<string, Product>();
    for (const p of products) {
      if (skip.has(p.product_id) || p.total_stock === 0) continue;
      const cur = best.get(p.category);
      if (!cur || p.total_stock > cur.total_stock) best.set(p.category, p);
    }
    return [...best.values()].sort((a, b) => b.total_stock - a.total_stock).slice(0, 4);
  }, [products]);

  const categories = useMemo(() => {
    const map = new Map<string, { cover: Product; count: number }>();
    for (const p of products) {
      const entry = map.get(p.category);
      if (entry) entry.count++;
      else map.set(p.category, { cover: p, count: 1 });
    }
    return [...map.entries()].sort((a, b) => b[1].count - a[1].count);
  }, [products]);

  const tees = products.filter((p) => p.category === "T-Shirts");
  const lowestPrice = tees.length ? Math.min(...tees.map((p) => p.price)) : null;

  return (
    <>
      {welcome && (
        <div className="container">
          <p className="notice welcome" role="status">
            Welcome, {user.first_name}! You're logged in.
          </p>
        </div>
      )}

      <section className="hero">
        <span className="blob blob-butter float-slow parallax" style={{ width: 90, height: 90, left: "-36px", top: "58%", ["--speed" as string]: 0.15 }} aria-hidden="true" />
        <span className="blob blob-coral float-slower parallax" style={{ width: 46, height: 46, left: "44%", bottom: "12%", ["--speed" as string]: 0.25 }} aria-hidden="true" />
        <svg className="squiggle spin-slow" style={{ right: "3%", top: "6%", width: 90 }} viewBox="0 0 100 100" aria-hidden="true">
          <path d="M50 5 L58 38 L95 50 L58 62 L50 95 L42 62 L5 50 L42 38 Z" fill="#2f5bff" />
        </svg>
        <div className="container hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">The New Haven Lookbook</p>
            <h1>
              <span className="line">Wear the</span>
              <span className="line">
                <span className="script">spirit</span> of
              </span>
              <span className="line">
                <span className="marker">Old Blue.</span>
              </span>
            </h1>
            <p className="lead">
              Hoodies, crewnecks, tees and quarter-zips for students, alumni and the families who cheer them on, all
              officially licensed and picked out right here on Broadway.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn btn-primary btn-lg btn-arrow">Shop Now</Link>
              <Link to="/about" className="btn btn-ghost btn-lg">Our story</Link>
            </div>
            <ul className="hero-perks">
              <li>Officially licensed</li>
              <li>Sizes XS–XXL</li>
              <li>Local New Haven shop</li>
            </ul>
          </div>

          <div className="hero-art" aria-label="A lookbook collage of Campus Customs products">
            <span className="stage-circle" aria-hidden="true" />
            <span className="stage-arch" aria-hidden="true" />
            {hero.length === 3 ? (
              <>
                <Link to={`/products/${hero[0].product_id}`} className="collage-card main">
                  <img src={hero[0].image_url} alt={hero[0].name} />
                </Link>
                <Link to={`/products/${hero[1].product_id}`} className="collage-card second">
                  <img src={hero[1].image_url} alt={hero[1].name} />
                </Link>
                <Link to={`/products/${hero[2].product_id}`} className="collage-card third">
                  <img src={hero[2].image_url} alt={hero[2].name} />
                </Link>
              </>
            ) : (
              <div className="hero-placeholder" aria-hidden="true" />
            )}
            {lowestPrice !== null && (
              <div className="price-sticker" aria-label={`Prices from ${formatPrice(lowestPrice)}`}>
                <span>
                  Tees from
                  <strong>{formatPrice(lowestPrice).replace(".00", "")}</strong>
                </span>
              </div>
            )}
          </div>
        </div>
      </section>

      <div className="marquee-wrap" aria-hidden="true">
        <div className="marquee">
          <div className="marquee-track">
            {[...MARQUEE, ...MARQUEE].map((m, i) => (
              <span key={i}>{m}</span>
            ))}
          </div>
        </div>
      </div>

      <section className="section container">
        <div className="section-head reveal">
          <div>
            <p className="eyebrow">Fan favorites</p>
            <h2>
              Featured <em>picks</em>
            </h2>
          </div>
          <Link to="/products" className="text-link">View all →</Link>
        </div>
        {error ? (
          <div className="notice notice-error state-box" role="alert">
            <strong>We couldn't load products right now.</strong>
            <p>Please check your connection and refresh the page.</p>
          </div>
        ) : featured.length === 0 ? (
          <>
            <p className="loading-text" role="status">Loading our favorites…</p>
            <div className="grid">{Array.from({ length: 4 }, (_, i) => <div key={i} className="skeleton-card" />)}</div>
          </>
        ) : (
          <div className="grid grid-4">
            {featured.map((p, i) => (
              <div key={p.product_id} className="reveal" style={stagger(i)}>
                <ProductCard product={p} />
              </div>
            ))}
          </div>
        )}
      </section>

      {categories.length > 0 && (
        <section className="section container">
          <div className="section-head reveal">
            <div>
              <p className="eyebrow">Find your fit</p>
              <h2>
                Shop by <em>category</em>
              </h2>
            </div>
          </div>
          <div className="category-grid">
            {categories.map(([name, { cover, count }], i) => (
              <Link
                key={name}
                to={`/products?category=${encodeURIComponent(name)}`}
                className="category-tile reveal"
                style={stagger(i)}
              >
                <img src={cover.image_url} alt="" loading="lazy" />
                <span>
                  {name}
                  <small>
                    {CATEGORY_BLURBS[name] ?? "Shop now"} · {count} styles
                  </small>
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="section container">
        <div className="feature-band reveal">
          <span className="blob blob-electric float-slow" style={{ width: 260, height: 260, right: -60, top: -110 }} aria-hidden="true" />
          <span className="blob blob-coral float-slower" style={{ width: 110, height: 110, right: 200, bottom: -55 }} aria-hidden="true" />
          <div>
            <p className="eyebrow" style={{ color: "var(--butter)" }}>Game day ready</p>
            <h2>
              Bundle up for <em>The Game.</em>
            </h2>
            <p>
              From the Harvard–Yale rivalry tee to fleece and quarter-zips, we've got you covered from the tailgate to the
              final whistle.
            </p>
          </div>
          <Link to="/products?q=football" className="btn btn-primary btn-lg btn-arrow">Shop game day</Link>
        </div>
      </section>

      {fresh.length > 0 && (
        <section className="section container">
          <div className="section-head reveal">
            <div>
              <p className="eyebrow">Fresh picks</p>
              <h2>
                Something for <em>everyone</em>
              </h2>
              <p className="muted" style={{ margin: "0.6rem 0 0" }}>One standout from each corner of the shop, all in stock now.</p>
            </div>
            <Link to="/products" className="text-link">Browse everything →</Link>
          </div>
          <div className="grid grid-4">
            {fresh.map((p, i) => (
              <div key={p.product_id} className="reveal" style={stagger(i)}>
                <ProductCard product={p} />
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="section container visit">
        <div className="reveal">
          <p className="eyebrow">Come say hi</p>
          <h2>
            Visit our <em style={{ color: "var(--coral)", fontWeight: 400 }}>New Haven</em> shop
          </h2>
          <p className="muted">
            Stop by to try things on, ask about sizing, or just talk Bulldogs with us. We're a short walk from campus.
          </p>
        </div>
        <address className="visit-card reveal" style={stagger(1)}>
          <strong>Campus Customs</strong>
          <span>
            57 Broadway
            <br />
            New Haven, CT
          </span>
        </address>
      </section>
    </>
  );
}
