import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthContext } from "../lib/authContext";
import { Insignia } from "./Insignia";

function joinClassNames(...items: Array<string | false | null | undefined>) {
  return items.filter(Boolean).join(" ");
}

export function SiteLayout() {
  const auth = useAuthContext();
  const location = useLocation();
  const navigate = useNavigate();
  const isDashboard = location.pathname.startsWith("/dashboard");

  return (
    <div className="site-shell">
      <header className="topbar-shell">
        <div className="topbar">
        <Link className="brand-lockup" to="/" aria-label="Home">
          <div className="brand-mark">
            <Insignia title="FinSentinel" />
          </div>
          <div className="brand-copy">
            <strong>FinSentinel</strong>
            <span>Signal desk for NIFTY 50</span>
          </div>
        </Link>

        <nav className="topnav" aria-label="Primary">
          <NavLink to="/" end className={({ isActive }) => joinClassNames("nav-link", isActive && "active")}>
            Platform
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => joinClassNames("nav-link", isActive && "active")}>
            About
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => joinClassNames("nav-link", isActive && "active")}>
            App
          </NavLink>
        </nav>

        <div className="topbar-actions">
          {auth.user ? (
            <>
              <span className="user-pill" title={auth.user.email}>
                {auth.user.email}
              </span>
              <button
                className="secondary-button"
                onClick={async () => {
                  await auth.logout();
                  navigate("/");
                }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <button className="secondary-button" onClick={() => navigate("/about")}>
                Learn more
              </button>
              <button className="primary-button" onClick={() => navigate("/login")}>
                Sign in
              </button>
            </>
          )}
        </div>
        </div>

        {isDashboard ? (
          <nav className="subnav" aria-label="Dashboard sections">
            <a className="subnav-link" href="#overview">
              Overview
            </a>
            <a className="subnav-link" href="#analysis">
              Analysis
            </a>
            <a className="subnav-link" href="#news">
              News
            </a>
            <a className="subnav-link" href="#alerts">
              Alerts
            </a>
            <a className="subnav-link" href="#portfolio">
              Portfolio
            </a>
          </nav>
        ) : null}
      </header>

      <main className="site-main">
        <Outlet />
      </main>

      <footer className="page-footer">
        <span>Explainable market signals for NIFTY 50.</span>
        <span className="footer-dot" aria-hidden="true">
          •
        </span>
        <span className="mono">FinSentinel</span>
      </footer>
    </div>
  );
}
