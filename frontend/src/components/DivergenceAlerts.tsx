import type { DivergenceSnapshot, PortfolioResponse } from "../types";


interface DivergenceAlertsProps {
  ticker: string;
  selected: DivergenceSnapshot | null;
  portfolio: PortfolioResponse | null;
}


export function DivergenceAlerts({ ticker, selected, portfolio }: DivergenceAlertsProps) {
  const alerts = [
    ...(selected
      ? [
          {
            ticker,
            severity: selected.severity,
            score: selected.divergence_score,
            mismatch: selected.signal_mismatch
          }
        ]
      : []),
    ...(
      portfolio?.holdings
        .filter((holding) => holding.divergence.severity !== "low" || holding.divergence.signal_mismatch)
        .map((holding) => ({
          ticker: holding.ticker,
          severity: holding.divergence.severity,
          score: holding.divergence.divergence_score,
          mismatch: holding.divergence.signal_mismatch
        })) || []
    )
  ];

  return (
    <section className="glass-card alerts-card">
      <div className="panel-header">
        <div>
          <div className="section-kicker">Divergence Alerts</div>
          <h2>Trust check</h2>
        </div>
        <p>Flags when sentiment and price direction start disagreeing.</p>
      </div>

      <div className="alerts-list">
        {alerts.length === 0 ? (
          <div className="empty-state">No active divergence alerts right now.</div>
        ) : (
          alerts.map((alert) => (
            <div key={`${alert.ticker}-${alert.score}`} className={`alert-row severity-${alert.severity}`}>
              <div>
                <strong>{alert.ticker}</strong>
                <p>{alert.mismatch ? "Sentiment is moving against price direction." : "Divergence is elevated but not yet inverted."}</p>
              </div>
              <div className="alert-metrics">
                <span>{alert.severity}</span>
                <strong>{alert.score.toFixed(3)}</strong>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
