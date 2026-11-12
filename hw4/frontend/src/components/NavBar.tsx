import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { useToast } from "../toast";

// Only true, checkable facts in the scrolling announcement bar.
const ANNOUNCEMENTS = [
  "Officially licensed Yale apparel",
  "Visit us at 57 Broadway, New Haven",
  "Sizes XS to XXL",
  "Ask our shopping assistant anytime",
  "Hoodies · Crewnecks · Tees · Quarter-zips · Fleece",
];

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/products", label: "Products" },
  { to: "/about", label: "About Us" },
];

export default function NavBar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, loading, logout } = useAuth();
  const toast = useToast();

  // Close the mobile menu whenever the page changes.
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  return (
    <header className="site-header">
      <div className="announcement" role="note" aria-label="Store announcements">
        {/* The list is repeated so the scrolling loop is seamless. */}
        <div className="announcement-track">
          {[...ANNOUNCEMENTS, ...ANNOUNCEMENTS].map((a, i) => (
            <span key={i} aria-hidden={i >= ANNOUNCEMENTS.length}>
              {a}
            </span>
          ))}
        </div>
      </div>
      <div className="nav-shell">
      <nav className="nav container" aria-label="Main">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <span className="brand-mark" aria-hidden="true">CC</span>
          <span>
            <span className="brand-text">
              Campus <em>Customs</em>
            </span>
            <span className="brand-sub">New Haven · Est. on Broadway</span>
          </span>
        </Link>

        <button
          className="menu-toggle"
          aria-expanded={open}
          aria-controls="nav-menu"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((o) => !o)}
        >
          <span />
          <span />
          <span />
        </button>

        <div id="nav-menu" className={`nav-menu ${open ? "open" : ""}`}>
          <ul className="nav-links">
            {links.map((l) => (
              <li key={l.to}>
                <NavLink to={l.to} end={l.end}>
                  {l.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <div className="nav-actions" aria-busy={loading}>
            {user ? (
              <>
                <span className="nav-greeting" title={user.email}>
                  Hi, <strong>{user.first_name}</strong>
                </span>
                <button
                  className="btn btn-ghost"
                  onClick={async () => {
                    await logout();
                    toast("You're logged out. See you soon!", "success");
                    navigate("/");
                  }}
                >
                  Log Out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className="btn btn-ghost">
                  Log In
                </NavLink>
                <NavLink to="/signup" className="btn btn-primary">
                  Create Account
                </NavLink>
              </>
            )}
          </div>
        </div>
      </nav>
      </div>
    </header>
  );
}
