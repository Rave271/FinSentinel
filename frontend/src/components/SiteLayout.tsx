import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuthContext } from "../lib/authContext";

function joinClassNames(...items: Array<string | false | null | undefined>) {
  return items.filter(Boolean).join(" ");
}

export function SiteLayout() {
  const auth = useAuthContext();
  const navigate = useNavigate();

  return (
    <div className="site-shell">
      <header className="topbar">
        <Link className="brand-lockup" to="/" aria-label="FinSentinel home">
          <div className="brand-mark" aria-hidden="true">
            FS
          </div>
          <div className="brand-copy">
            <strong>FinSentinel</strong>
            <span>signal intelligence for the NIFTY 50</span>
          </div>
        </Link>

        <nav className="topnav" aria-label="Primary">
          <NavLink to="/" end className={({ isActive }) => joinClassNames("nav-link", isActive && "active")}>
            Home
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => joinClassNames("nav-link", isActive && "active")}>
            About
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => joinClassNames("nav-link", isActive && "active")}>
            Dashboard
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
            <button className="primary-button" onClick={() => navigate("/login")}>
              Sign in
            </button>
          )}
        </div>
      </header>

      <main className="site-main">
        <Outlet />
      </main>

      <footer className="page-footer">
        <span>FinSentinel — market sentiment, risk, and explainable signals.</span>
        <span className="footer-dot" aria-hidden="true">
          •
        </span>
        <span>Built by Raghav Verma (rave271).</span>
      </footer>
    </div>
  );
}

