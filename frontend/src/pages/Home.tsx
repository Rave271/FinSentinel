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
