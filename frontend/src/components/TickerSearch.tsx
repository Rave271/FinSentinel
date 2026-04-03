import type { KeyboardEvent } from "react";


interface TickerSearchProps {
  query: string;
  suggestions: string[];
  selectedTicker: string;
  supportedTickers: string[];
  onQueryChange: (value: string) => void;
  onSelectTicker: (ticker: string) => void;
}


export function TickerSearch({
  query,
  suggestions,
  selectedTicker,
  supportedTickers,
  onQueryChange,
  onSelectTicker
}: TickerSearchProps) {
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && query.trim()) {
      onSelectTicker(query.trim().toUpperCase());
    }
  }

  const featuredCoverage = supportedTickers.slice(0, 10).join(", ");

  return (
    <section className="search-panel glass-card">
      <div className="search-header">
        <div>
          <div className="section-kicker">Coverage Search</div>
          <h2>Load a supported company</h2>
          <p>Search by ticker and jump directly to the latest available signal snapshot.</p>
        </div>

        <div className="search-summary">
          <div className="search-summary-item">
            <span>Universe</span>
            <strong>{supportedTickers.length} names</strong>
          </div>
          <div className="search-summary-item">
            <span>Selected</span>
            <strong>{selectedTicker}</strong>
          </div>
        </div>
      </div>

      <div className="search-row">
        <label className="search-field">
          <span>Ticker</span>
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search RELIANCE, INFY, TCS..."
          />
        </label>
        <button className="primary-button" onClick={() => onSelectTicker(query.trim().toUpperCase())}>
          Load Signal
        </button>
      </div>

      <div className="suggestion-label">Quick access</div>
      <div className="suggestion-strip">
        {suggestions.map((ticker) => (
          <button
            key={ticker}
            className={ticker === selectedTicker ? "chip active" : "chip"}
            onClick={() => onSelectTicker(ticker)}
          >
            {ticker}
          </button>
        ))}
      </div>

      <p className="support-note">
        Coverage is currently limited to the trained NIFTY 50 universe. Examples include {featuredCoverage}.
      </p>
    </section>
  );
}
