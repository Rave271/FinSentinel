export type ThemeMode = "light" | "dark";

export type SignalLabel = "BUY" | "HOLD" | "SELL";
export type SentimentLabel = "positive" | "negative" | "neutral";
export type AlertSeverity = "low" | "medium" | "high";

export interface SignalProbabilityMap {
  BUY: number;
  HOLD: number;
  SELL: number;
}

export interface MarketSnapshot {
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  price_delta_1d: number;
  price_delta_5d: number;
}

export interface SentimentSnapshot {
  news: number;
  social: number;
  divergence: number;
}

export interface SignalSummary {
  label: SignalLabel;
  confidence: number;
  probabilities: SignalProbabilityMap;
}

export interface Narrative {
  headline: string;
  summary: string;
  details: string[];
}

export interface Factor {
  feature: string;
  label: string;
  value: number;
  display_value: string;
  shap_value: number;
  effect: "supports" | "tempers";
}

export interface DivergenceSnapshot {
  ticker: string;
  as_of: string;
  price_delta_1d: number;
  price_delta_normalized: number;
  news_sentiment: number;
  social_sentiment: number;
  composite_sentiment: number;
  divergence_score: number;
  severity: AlertSeverity;
  signal_mismatch: boolean;
}

export interface SignalResponse {
  ticker: string;
  as_of: string;
  market: MarketSnapshot;
  sentiment: SentimentSnapshot;
  signal: SignalSummary;
  narrative: Narrative;
  top_factors: Factor[];
  divergence: DivergenceSnapshot;
}

export interface NewsItem {
  headline: string;
  source: string;
  published_at: string;
  url: string;
  sentiment: {
    label: SentimentLabel;
    score: number;
  };
}

export interface NewsResponse {
  ticker: string;
  items: NewsItem[];
}

export interface PortfolioHoldingInput {
  ticker: string;
  quantity: number;
  average_cost?: number;
}

export interface PortfolioHolding {
  ticker: string;
  quantity: number;
  average_cost: number | null;
  market_value: number;
  unrealized_pnl: number | null;
  signal: SignalSummary;
  divergence: DivergenceSnapshot;
}

export interface PortfolioResponse {
  user: string;
  portfolio_size: number;
  total_market_value: number;
  signal_mix: SignalProbabilityMap;
  risk_level: "low" | "medium" | "high";
  holdings: PortfolioHolding[];
}

export interface LivePayload {
  ticker: string;
  type: string;
  as_of: string;
  market: MarketSnapshot;
  signal: SignalSummary;
  divergence: DivergenceSnapshot;
  sentiment: SentimentSnapshot;
}
