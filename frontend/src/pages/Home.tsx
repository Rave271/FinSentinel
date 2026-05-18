import { Link } from "react-router-dom";

import { useAuthContext } from "../lib/authContext";
import { GridWire } from "../components/GridWire";

export function HomePage() {
  const auth = useAuthContext();

  return (
    <section className="home-hero">
      <div className="home-hero-surface">
        <div className="home-hero-copy">
          <span className="eyebrow">Market Intelligence</span>
          <h1>A calmer signal desk for NIFTY 50 monitoring.</h1>
          <p>
            FinSentinel brings price snapshots, sentiment, model signals, and divergence checks into one workspace so
            you can answer “what changed, why, and how confident are we?” quickly.
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
              <span>Workflow</span>
              <strong>Operator-first</strong>
              <small>Overview → drivers → news → alerts</small>
            </div>
          </div>
        </div>

        <div className="home-hero-art" aria-hidden="true">
          <GridWire title="Neon gridwire" />
          <div className="neon-pane" />
          <div className="marble-chip marble-chip--a" />
          <div className="marble-chip marble-chip--b" />
          <div className="marble-chip marble-chip--c" />
        </div>
      </div>
    </section>
  );
}
