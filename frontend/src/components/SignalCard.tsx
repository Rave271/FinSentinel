import type { SignalResponse } from "../types";


interface SignalCardProps {
  signal: SignalResponse;
}


function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

function formatChange(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${(value * 100).toFixed(2)}%`;
}

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0
  }).format(value);
}

function formatDateTime(timestamp: string) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "Awaiting timestamp";
  }
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  });
}


export function SignalCard({ signal }: SignalCardProps) {
  const compositeSentiment = Number(((signal.sentiment.news + signal.sentiment.social) / 2).toFixed(3));
  const leadFactor = signal.top_factors[0];

  return (
    <section className="signal-card hero-card">
      <div className="signal-card-top">
        <div className="hero-copy">
          <div className="section-kicker">Current Recommendation</div>
          <div className="signal-heading-row">
            <h1>{signal.ticker}</h1>
            <span className={`signal-badge ${signal.signal.label.toLowerCase()}`}>{signal.signal.label}</span>
          </div>
          <p className="hero-headline">{signal.narrative.headline}</p>
          <p className="hero-summary">{signal.narrative.summary}</p>

          <div className="signal-meta-row">
            <span>Updated {formatDateTime(signal.as_of)}</span>
            <span>Volume {formatNumber(signal.market.volume)}</span>
            <span>Divergence {signal.divergence.severity}</span>
          </div>
        </div>

        <div className="signal-side-panel">
          <span className="signal-side-label">Composite Sentiment</span>
          <strong>{compositeSentiment.toFixed(3)}</strong>
          <p>
            {leadFactor
              ? `${leadFactor.label} is currently the strongest ${leadFactor.effect === "supports" ? "supporting" : "offsetting"} factor.`
              : "Explainability factors will appear as they are computed."}
          </p>
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <span>Confidence</span>
          <strong>{formatPercent(signal.signal.confidence)}</strong>
        </div>
        <div className="metric-card">
          <span>Last Price</span>
          <strong>{signal.market.close.toFixed(2)}</strong>
        </div>
        <div className="metric-card">
          <span>1D Move</span>
          <strong>{formatChange(signal.market.price_delta_1d)}</strong>
        </div>
        <div className="metric-card">
          <span>5D Move</span>
          <strong>{formatChange(signal.market.price_delta_5d)}</strong>
        </div>
      </div>

      <div className="probability-row">
        {Object.entries(signal.signal.probabilities).map(([label, value]) => (
          <div key={label} className="probability-card">
            <div className="probability-copy">
              <span>{label}</span>
              <strong>{formatPercent(value)}</strong>
            </div>
            <div className="probability-track">
              <div className={`probability-fill ${label.toLowerCase()}`} style={{ width: `${value * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
