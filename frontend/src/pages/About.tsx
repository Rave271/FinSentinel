export function AboutPage() {
  return (
    <section className="content-page">
      <div className="content-surface">
        <span className="eyebrow">About</span>
        <h1>FinSentinel in brief</h1>
        <p>
          FinSentinel combines market price snapshots, news and social sentiment, and model-driven signal
          outputs into a single operator-friendly dashboard for the NIFTY 50. The goal is to replace reactive
          chart-watching with an explainable layer that answers: what moved, why it moved, and how confident we
          are.
        </p>

        <div className="about-grid">
          <div className="glass-card about-card">
            <h2>What it does</h2>
            <ul>
              <li>Signal snapshot per ticker (label + confidence)</li>
              <li>News feed + sentiment blending</li>
              <li>Divergence alerts when signal and market disagree</li>
              <li>Portfolio analyzer for quick risk review</li>
              <li>Live websocket pulse for ongoing monitoring</li>
            </ul>
          </div>

          <div className="glass-card about-card">
            <h2>Who built it</h2>
            <p>
              <strong>Raghav Verma</strong>
              <br />
              GitHub: <span className="mono">rave271</span>
            </p>
            <p className="muted">
              This build focuses on an abstract, modern UI: creamy marble whites, transparent crimson accents,
              and subtle Greek-statue linework as a motif.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

