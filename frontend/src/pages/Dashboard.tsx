import { startTransition, useDeferredValue, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { DivergenceAlerts } from "../components/DivergenceAlerts";
import { LivePulseChart } from "../components/LivePulseChart";
import { NewsFeedPanel } from "../components/NewsFeedPanel";
import { PortfolioAnalyzer } from "../components/PortfolioAnalyzer";
import { ShapFactorsChart } from "../components/ShapFactorsChart";
import { SignalCard } from "../components/SignalCard";
import { TickerSearch } from "../components/TickerSearch";
import { TICKERS } from "../data/tickers";
import { buildWebsocketUrl, fetchDivergence, fetchNews, fetchSignal, type LivePayload } from "../lib/api";
import { useAuthContext } from "../lib/authContext";
import type { DivergenceSnapshot, NewsItem, PortfolioResponse, SignalResponse, ThemeMode } from "../types";

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
  const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(timestamp);
  if (isDateOnly) {
    const [year, month, day] = timestamp.split("-").map((part) => Number(part));
    const date = new Date(Date.UTC(year, month - 1, day));
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
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
  const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(timestamp);
  if (isDateOnly) {
    const [year, month, day] = timestamp.split("-").map((part) => Number(part));
    const date = new Date(Date.UTC(year, month - 1, day));
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
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

export function DashboardPage() {
  const auth = useAuthContext();
  const location = useLocation();
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
    if (!auth.user) {
      return;
    }

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
  }, [auth.user, selectedTicker]);

  useEffect(() => {
    if (!auth.user) {
      return;
    }

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
  }, [auth.user, selectedTicker]);

  function handleSelectTicker(nextTicker: string) {
    if (!nextTicker) {
      return;
    }
    const normalized = nextTicker.toUpperCase();
    if (!TICKERS.includes(normalized)) {
      setError(`${normalized} is not in the current trained universe yet. Try one of: ${TICKERS.join(", ")}.`);
      return;
    }
    startTransition(() => {
      setSelectedTicker(normalized);
      setQuery(normalized);
      setPortfolio(null);
      setError(null);
    });
  }

  if (!auth.user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return (
    <div className="dashboard-shell">
      <section className="dashboard-hero">
        <section className="glass-card hero-intro">
          <div className="page-header">
            <div>
              <span className="eyebrow">Market Desk</span>
              <h1>Signals, sentiment, and divergence—without the noise.</h1>
              <p>
                Browse the trained universe, watch live pulse updates, and sanity-check sentiment drift against
                model confidence.
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

          <div className="dashboard-hero-actions">
            <div className={`status-indicator ${connectionState}`}>Feed {connectionLabel(connectionState)}</div>
            <button className="chip-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
              Theme: {theme === "dark" ? "Noir" : "Marble"}
            </button>
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
      {signal?.data_status?.age_days != null && signal.data_status.age_days > 3 ? (
        <div className="loading-panel">
          Data snapshot is {signal.data_status.age_days} days old (source: {signal.data_status.source}). Run the data
          pipeline / refresh `data/training_features.csv` on the backend to see current dates.
        </div>
      ) : null}
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
            <NewsFeedPanel id="news" items={news} />
            <DivergenceAlerts id="alerts" ticker={selectedTicker} selected={divergence} portfolio={portfolio} />
            <PortfolioAnalyzer
              id="portfolio"
              seedTicker={selectedTicker}
              suggestions={TICKERS}
              onAnalysis={setPortfolio}
              isAuthenticated={auth.user?.role !== "guest"}
            />

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
    </div>
  );
}
