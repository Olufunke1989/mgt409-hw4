import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="site-footer">
      <span className="blob blob-electric float-slower" style={{ width: 340, height: 340, right: -120, top: -140 }} aria-hidden="true" />
      <span className="blob blob-coral float-slow" style={{ width: 120, height: 120, left: "38%", top: -40 }} aria-hidden="true" />
      <div className="container">
        <div className="footer-cta">
          <h2>
            Made for the ones who <em>bleed blue.</em>
          </h2>
          <Link to="/products" className="btn btn-primary btn-lg btn-arrow">
            Shop the collection
          </Link>
        </div>
        <div className="footer-grid">
          <div>
            <p className="footer-brand brand-text">
              Campus <em>Customs</em>
            </p>
            <p className="muted">
              Officially licensed Yale apparel, picked by people who love New Haven as much as you do.
            </p>
          </div>
          <div>
            <h3>Shop</h3>
            <ul>
              <li><Link to="/products">All products</Link></li>
              <li><Link to="/products?category=Hoodies">Hoodies</Link></li>
              <li><Link to="/products?category=Crewnecks">Crewnecks</Link></li>
              <li><Link to="/products?category=T-Shirts">T-shirts</Link></li>
              <li><Link to="/products?category=Quarter-Zips">Quarter-zips</Link></li>
            </ul>
          </div>
          <div>
            <h3>Visit</h3>
            <address>
              Campus Customs
              <br />
              57 Broadway
              <br />
              New Haven, CT
            </address>
          </div>
          <div>
            <h3>Account</h3>
            <ul>
              <li><Link to="/login">Log in</Link></li>
              <li><Link to="/signup">Create account</Link></li>
              <li><Link to="/about">Our story</Link></li>
            </ul>
          </div>
        </div>
        <p className="footer-wordmark" aria-hidden="true">Campus Customs</p>
        <p className="fine-print">
          <span>© {new Date().getFullYear()} Campus Customs. Built for a Yale course project.</span>
          <span>Officially licensed Yale merchandise</span>
        </p>
      </div>
    </footer>
  );
}
