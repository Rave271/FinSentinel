import { useEffect, useState } from "react";

import { analyzePortfolio, fetchDevToken } from "../lib/api";
import type { PortfolioHoldingInput, PortfolioResponse } from "../types";


interface PortfolioAnalyzerProps {
  seedTicker: string;
  suggestions: string[];
  onAnalysis: (portfolio: PortfolioResponse | null) => void;
}

interface DraftHolding {
  ticker: string;
  quantity: string;
  average_cost: string;
}


export function PortfolioAnalyzer({ seedTicker, suggestions, onAnalysis }: PortfolioAnalyzerProps) {
  const [rows, setRows] = useState<DraftHolding[]>([{ ticker: seedTicker, quantity: "8", average_cost: "1500" }]);
  const [token, setToken] = useState<string | null>(null);
  const [status, setStatus] = useState("Ready to analyze.");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setRows((current) => {
      if (current[0]?.ticker) {
        return current;
      }
      return [{ ticker: seedTicker, quantity: "8", average_cost: "1500" }];
    });
  }, [seedTicker]);

  function updateRow(index: number, field: keyof DraftHolding, value: string) {
    setRows((current) =>
      current.map((row, rowIndex) => (rowIndex === index ? { ...row, [field]: value.toUpperCase() } : row))
    );
  }

  function addRow() {
    setRows((current) => [...current, { ticker: "", quantity: "0", average_cost: "" }]);
  }

  async function handleAnalyze() {
    const holdings: PortfolioHoldingInput[] = rows
      .filter((row) => row.ticker.trim() && Number(row.quantity) > 0)
      .map((row) => ({
        ticker: row.ticker.trim().toUpperCase(),
        quantity: Number(row.quantity),
        average_cost: row.average_cost ? Number(row.average_cost) : undefined
      }));

    if (holdings.length === 0) {
      setStatus("Add at least one valid holding first.");
      onAnalysis(null);
      return;
    }

    setLoading(true);
    setStatus("Requesting a dev token and scoring the portfolio...");

    try {
      let activeToken = token;
      if (!activeToken) {
        const auth = await fetchDevToken();
        activeToken = auth.access_token;
        setToken(activeToken);
      }
      const result = await analyzePortfolio(activeToken, holdings);
      onAnalysis(result);
      setStatus(`Risk layer updated for ${result.portfolio_size} holdings.`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Portfolio analysis failed";
      setStatus(message);
      onAnalysis(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="glass-card portfolio-card">
      <div className="panel-header">
        <div>
          <div className="section-kicker">Portfolio Lens</div>
          <h2>Personalized risk dashboard</h2>
        </div>
        <p>{status}</p>
      </div>

      <div className="portfolio-form">
        {rows.map((row, index) => (
          <div key={`${row.ticker}-${index}`} className="holding-row">
            <label>
              <span>Ticker</span>
              <input
                list="ticker-options"
                value={row.ticker}
                onChange={(event) => updateRow(index, "ticker", event.target.value)}
              />
            </label>
            <label>
              <span>Qty</span>
              <input
                type="number"
                min="0"
                step="1"
                value={row.quantity}
                onChange={(event) => updateRow(index, "quantity", event.target.value)}
              />
            </label>
            <label>
              <span>Avg Cost</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={row.average_cost}
                onChange={(event) => updateRow(index, "average_cost", event.target.value)}
              />
            </label>
          </div>
        ))}

        <datalist id="ticker-options">
          {suggestions.map((ticker) => (
            <option key={ticker} value={ticker} />
          ))}
        </datalist>

        <div className="portfolio-actions">
          <button className="secondary-button" onClick={addRow}>
            Add Holding
          </button>
          <button className="primary-button" onClick={handleAnalyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Portfolio"}
          </button>
        </div>
      </div>
    </section>
  );
}
