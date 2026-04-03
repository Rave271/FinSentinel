import { startTransition, useDeferredValue, useEffect, useState } from "react";

import { DivergenceAlerts } from "./components/DivergenceAlerts";
import { LivePulseChart } from "./components/LivePulseChart";
import { NewsFeedPanel } from "./components/NewsFeedPanel";
import { PortfolioAnalyzer } from "./components/PortfolioAnalyzer";
import { ShapFactorsChart } from "./components/ShapFactorsChart";
import { SignalCard } from "./components/SignalCard";
import { TickerSearch } from "./components/TickerSearch";
import { TICKERS } from "./data/tickers";
import { buildWebsocketUrl, fetchDivergence, fetchNews, fetchSignal, type LivePayload } from "./lib/api";
import type { DivergenceSnapshot, NewsItem, PortfolioResponse, SignalResponse, ThemeMode } from "./types";


interface LivePoint {
  time: string;
  price: number;
  sentiment: number;
}


function detectTheme(): ThemeMode {
  const saved = window.localStorage.getItem("finsentinel-theme");
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}


function formatClock(timestamp: string) {
  if (!timestamp) {
    return "Now";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "Now";
  }
  return date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatDateTime(timestamp: string) {
  if (!timestamp) {
    return "Awaiting update";
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "Awaiting update";
  }
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function formatPrice(value: number) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2
  }).format(value);
}

function formatPercent(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${(value * 100).toFixed(2)}%`;
}

function connectionLabel(connectionState: string) {
  switch (connectionState) {
    case "live":
      return "Live";
    case "degraded":
      return "Degraded";
    case "offline":
      return "Offline";
    default:
      return "Connecting";
  }
}


export default function App() {
  const [theme, setTheme] = useState<ThemeMode>(() => detectTheme());
  const [query, setQuery] = useState("INFY");
  const [selectedTicker, setSelectedTicker] = useState("INFY");
  const [signal, setSignal] = useState<SignalResponse | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [divergence, setDivergence] = useState<DivergenceSnapshot | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [livePoints, setLivePoints] = useState<LivePoint[]>([]);
  const [connectionState, setConnectionState] = useState("connecting");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const deferredQuery = useDeferredValue(query);
  const suggestions = TICKERS.filter((ticker) => ticker.includes(deferredQuery.trim().toUpperCase())).slice(0, 8);
  const compositeSentiment = signal
    ? Number(((signal.sentiment.news + signal.sentiment.social) / 2).toFixed(3))
    : null;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("finsentinel-theme", theme);
  }, [theme]);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const [signalPayload, newsPayload, divergencePayload] = await Promise.all([
          fetchSignal(selectedTicker),
          fetchNews(selectedTicker),
          fetchDivergence(selectedTicker)
        ]);
        if (cancelled) {
          return;
        }
        setSignal(signalPayload);
        setNews(newsPayload.items);
        setDivergence(divergencePayload);
        setLivePoints([
          {
            time: formatClock(signalPayload.as_of),
            price: signalPayload.market.close,
            sentiment: Number(((signalPayload.sentiment.news + signalPayload.sentiment.social) / 2).toFixed(3))
          }
        ]);
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [selectedTicker]);

  useEffect(() => {
    const socket = new WebSocket(buildWebsocketUrl(selectedTicker));
    setConnectionState("connecting");

    socket.onopen = () => setConnectionState("live");
    socket.onerror = () => setConnectionState("degraded");
    socket.onclose = () => setConnectionState("offline");
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as LivePayload;
      if (!payload.market) {
        return;
      }
      const point = {
        time: formatClock(payload.as_of),
        price: payload.market.close,
        sentiment: Number(((payload.sentiment.news + payload.sentiment.social) / 2).toFixed(3))
      };
      setLivePoints((current) => [...current.slice(-11), point]);
    };

    return () => {
      socket.close();
    };
  }, [selectedTicker]);

  function handleSelectTicker(nextTicker: string) {
    if (!nextTicker) {
      return;
    }
    const normalized = nextTicker.toUpperCase();
    if (!TICKERS.includes(normalized)) {
      setError(
        `${normalized} is not in the current trained universe yet. Try one of: ${TICKERS.join(", ")}.`
      );
      return;
    }
    startTransition(() => {
      setSelectedTicker(normalized);
      setQuery(normalized);
      setPortfolio(null);
      setError(null);
    });
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">FS</div>
          <div className="brand-copy">
            <strong>FinSentinel</strong>
            <span>NIFTY 50 signal intelligence</span>
          </div>
        </div>
        <div className="topnav" aria-label="Primary">
          <span>Overview</span>
          <span>Signals</span>
          <span>Portfolio</span>
        </div>
        <div className="topbar-actions">
          <div className={`status-indicator ${connectionState}`}>Feed {connectionLabel(connectionState)}</div>
          <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            {theme === "dark" ? "Light Mode" : "Dark Mode"}
          </button>
        </div>
      </header>

      <section className="hero-layout">
        <section className="hero-intro">
          <div className="page-header">
            <div>
              <span className="eyebrow">Market Intelligence Platform</span>
              <h1>Professional signal coverage for the NIFTY 50.</h1>
              <p>
                Monitor model conviction, price action, sentiment drift, and portfolio risk from a
                single operational dashboard designed for quick review.
              </p>
            </div>
          </div>

          <div className="hero-stat-grid">
            <div className="hero-stat-card">
              <span>Coverage</span>
              <strong>{TICKERS.length} stocks</strong>
              <small>Trained NIFTY 50 universe</small>
            </div>
            <div className="hero-stat-card">
              <span>Selected</span>
              <strong>{selectedTicker}</strong>
              <small>{signal ? signal.signal.label : "Loading latest signal"}</small>
            </div>
            <div className="hero-stat-card">
              <span>Last refresh</span>
              <strong>{signal ? formatClock(signal.as_of) : "..."}</strong>
              <small>{signal ? formatDateTime(signal.as_of) : "Waiting for market snapshot"}</small>
            </div>
          </div>
        </section>

        <TickerSearch
          query={query}
          suggestions={suggestions.length > 0 ? suggestions : TICKERS.slice(0, 6)}
          selectedTicker={selectedTicker}
          supportedTickers={TICKERS}
          onQueryChange={setQuery}
          onSelectTicker={handleSelectTicker}
        />
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {loading && !signal ? <div className="loading-panel">Loading the market lens...</div> : null}

      {signal ? (
        <>
          <section className="overview-strip" id="overview">
            <div className="overview-card">
              <span>Signal</span>
              <strong>{signal.signal.label}</strong>
              <small>{(signal.signal.confidence * 100).toFixed(1)}% confidence</small>
            </div>
            <div className="overview-card">
              <span>Last Price</span>
              <strong>{formatPrice(signal.market.close)}</strong>
              <small>{formatPercent(signal.market.price_delta_1d)} today</small>
            </div>
            <div className="overview-card">
              <span>Composite Sentiment</span>
              <strong>{compositeSentiment?.toFixed(3) ?? "0.000"}</strong>
              <small>News and social blended</small>
            </div>
            <div className="overview-card">
              <span>Divergence</span>
              <strong>{signal.divergence.severity}</strong>
              <small>{signal.divergence.signal_mismatch ? "Signal mismatch flagged" : "Model and market aligned"}</small>
            </div>
          </section>

          <SignalCard signal={signal} />

          <main className="dashboard-grid" id="analysis">
            <ShapFactorsChart factors={signal.top_factors} />
            <LivePulseChart points={livePoints} connectionState={connectionState} />
            <NewsFeedPanel items={news} />
            <DivergenceAlerts ticker={selectedTicker} selected={divergence} portfolio={portfolio} />
            <PortfolioAnalyzer seedTicker={selectedTicker} suggestions={TICKERS} onAnalysis={setPortfolio} />

            <section className="glass-card notes-card">
              <div className="panel-header">
                <div>
                  <div className="section-kicker">Model Reading</div>
                  <h2>Operator notes</h2>
                </div>
                <p>Plain-language context pulled from the current model output.</p>
              </div>

              <div className="notes-list">
                {signal.narrative.details.map((detail) => (
                  <div key={detail} className="note-chip">
                    {detail}
                  </div>
                ))}
              </div>

              {portfolio ? (
                <div className="portfolio-summary">
                  <div className="summary-card">
                    <span>Portfolio risk</span>
                    <strong>{portfolio.risk_level}</strong>
                  </div>
                  <div className="summary-card">
                    <span>Total market value</span>
                    <strong>{portfolio.total_market_value.toFixed(2)}</strong>
                  </div>
                  <div className="summary-card">
                    <span>Holdings scanned</span>
                    <strong>{portfolio.portfolio_size}</strong>
                  </div>
                </div>
              ) : null}
            </section>
          </main>
        </>
      ) : null}

      <footer className="page-footer">
        FinSentinel combines model output, market context, and risk review into a single desk-ready
        interface for supported NIFTY 50 names.
      </footer>
    </div>
  );
}
