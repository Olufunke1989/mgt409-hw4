import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProduct } from "../api";
import type { ProductDetail } from "../types";

const values = [
  {
    title: "Made for Yale people",
    text: "Students, grads, parents and lifelong fans. We stock the pieces our neighbors actually want to wear, from residential college gear to varsity sports.",
  },
  {
    title: "Officially licensed",
    text: "Every logo and wordmark is licensed, so you know you're getting the real thing and supporting the university community.",
  },
  {
    title: "Rooted in New Haven",
    text: "We're a local shop on Broadway, a few minutes' walk from Old Campus. When you shop with us, you're supporting a New Haven business.",
  },
];

// Two real catalogue photos for the collage.
const ART_IDS = ["yale-mom-hoodie", "davenport-college-crewneck"];

export default function About() {
  const [art, setArt] = useState<ProductDetail[]>([]);

  useEffect(() => {
    Promise.all(ART_IDS.map((id) => fetchProduct(id).catch(() => null))).then((list) =>
      setArt(list.filter((p): p is ProductDetail => Boolean(p))),
    );
  }, []);

  return (
    <div className="container page">
      <section className="about-hero">
        <header className="about-head">
          <p className="eyebrow">Our story</p>
          <h1>
            Blue and white, from <em>right down the street.</em>
          </h1>
          <p className="lead">
            Campus Customs started with a simple idea: Yale fans deserve apparel that feels as good as it looks. From our
            shop at 57 Broadway, we've been outfitting first-years on move-in day, alumni coming back for reunions, and
            families cheering at The Game.
          </p>
        </header>
        <div className="about-art" aria-hidden={art.length === 0}>
          <span className="blob blob-lavender" style={{ inset: "8% 6% 6% 8%" }} aria-hidden="true" />
          <span className="blob blob-butter float-slow" style={{ width: 70, height: 70, right: "2%", top: "4%" }} aria-hidden="true" />
          <span className="blob blob-coral float-slower" style={{ width: 40, height: 40, left: "2%", bottom: "10%" }} aria-hidden="true" />
          {art.map((p, i) => (
            <Link key={p.product_id} to={`/products/${p.product_id}`} className={`collage-card ${i === 0 ? "a1" : "a2"}`}>
              <img src={p.image_url} alt={p.name} />
            </Link>
          ))}
        </div>
      </section>

      <section className="value-grid">
        {values.map((v, i) => (
          <article key={v.title} className="value-card reveal" style={{ "--delay": `${i * 0.08}s` } as React.CSSProperties}>
            <span className="num">0{i + 1}</span>
            <h2>{v.title}</h2>
            <p className="muted">{v.text}</p>
          </article>
        ))}
      </section>

      <section className="about-split">
        <div className="reveal">
          <h2>What you'll find</h2>
          <p className="muted">
            Cozy hoodies and crewnecks, everyday tees, quarter-zips for chilly walks to class, and jackets for game day.
            We carry gear for many of the residential colleges and varsity teams, plus classic Yale designs that never go
            out of style.
          </p>
        </div>
        <div className="reveal" style={{ "--delay": "0.08s" } as React.CSSProperties}>
          <h2>Need help choosing?</h2>
          <p className="muted">
            Every product page lists the sizes we have in stock, and our shopping assistant (the "Ask us" button in the
            corner) is happy to help you find a gift or the right fit. You're always welcome to stop by and ask us, too.
          </p>
        </div>
      </section>

      <div className="feature-band reveal">
        <span className="blob blob-electric float-slow" style={{ width: 220, height: 220, right: -50, top: -90 }} aria-hidden="true" />
        <span className="blob blob-butter float-slower" style={{ width: 80, height: 80, right: 180, bottom: -40 }} aria-hidden="true" />
        <div>
          <h2>
            Ready to rep the <em>Bulldogs?</em>
          </h2>
          <p>Browse the full collection and find your new favorite.</p>
        </div>
        <Link to="/products" className="btn btn-primary btn-lg btn-arrow">Shop now</Link>
      </div>
    </div>
  );
}
