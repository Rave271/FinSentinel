import { Link } from "react-router-dom";

import { useAuthContext } from "../lib/authContext";

function StatueBackdrop() {
  return (
    <svg className="statue-backdrop" viewBox="0 0 720 540" role="img" aria-label="Abstract statue illustration">
      <defs>
        <linearGradient id="fs-crimson" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="rgba(172, 35, 44, 0.0)" />
          <stop offset="0.45" stopColor="rgba(172, 35, 44, 0.55)" />
          <stop offset="1" stopColor="rgba(172, 35, 44, 0.0)" />
        </linearGradient>
        <filter id="fs-blur" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="1.35" />
        </filter>
      </defs>

      <g fill="none" stroke="url(#fs-crimson)" strokeWidth="2.4" filter="url(#fs-blur)">
        <path d="M412 112c38 14 62 44 70 85 8 44-2 85-25 118-10 14-23 26-39 34" />
        <path d="M299 168c-8 26-5 54 10 84 17 35 39 60 66 75 16 9 33 13 52 13" />
        <path d="M280 202c-18 30-22 62-10 96 14 40 38 69 71 88 25 14 54 20 87 18" />
        <path d="M254 392c44 40 109 56 194 48 52-5 93-20 122-44" />
        <path d="M190 472c86-38 170-51 252-39 56 8 96 23 120 46" />
        <path d="M468 144c-6 20-17 34-34 44-18 10-36 14-56 12" />
        <path d="M353 206c18-18 39-25 64-22 22 3 41 13 56 30" />
      </g>
    </svg>
  );
}

export function HomePage() {
  const auth = useAuthContext();

  return (
    <section className="home-hero">
      <div className="home-hero-surface">
        <div className="home-hero-copy">
          <span className="eyebrow">FinSentinel</span>
          <h1>Creme marble UX for market signal ops.</h1>
          <p>
            A modern, explainable dashboard for NIFTY 50 signals: sentiment drift, factor drivers,
            divergence alerts, and portfolio risk—built to feel like a calm trading desk, not a noisy terminal.
          </p>

          <div className="home-cta">
            {auth.user ? (
              <Link className="primary-button" to="/dashboard">
                Open dashboard
              </Link>
            ) : (
              <Link className="primary-button" to="/login">
                Sign in
              </Link>
            )}
            <Link className="secondary-button" to="/about">
              About the project
            </Link>
          </div>

          <div className="home-meta-grid">
            <div className="meta-card">
              <span>Signal stack</span>
              <strong>FastAPI + React</strong>
              <small>HttpOnly sessions, live websocket pulse</small>
            </div>
            <div className="meta-card">
              <span>Coverage</span>
              <strong>NIFTY 50</strong>
              <small>Trained universe + explainability</small>
            </div>
            <div className="meta-card">
              <span>Aesthetic</span>
              <strong>Marble + crimson</strong>
              <small>Greek statue motifs, translucent layers</small>
            </div>
          </div>
        </div>

        <div className="home-hero-art" aria-hidden="true">
          <StatueBackdrop />
          <div className="crimson-pane" />
          <div className="marble-chip marble-chip--a" />
          <div className="marble-chip marble-chip--b" />
          <div className="marble-chip marble-chip--c" />
        </div>
      </div>
    </section>
  );
}

