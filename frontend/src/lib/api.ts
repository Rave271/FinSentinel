import type {
  DivergenceSnapshot,
  LivePayload,
  NewsResponse,
  PortfolioHoldingInput,
  PortfolioResponse,
  SignalResponse
} from "../types";


const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    ...init
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Ignore JSON parse failures and use the default status text.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}


export function getApiBaseUrl() {
  return API_BASE_URL;
}


export function buildWebsocketUrl(ticker: string) {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/live/${ticker.toUpperCase()}`;
  url.search = "";
  return url.toString();
}


export function fetchSignal(ticker: string) {
  return request<SignalResponse>(`/api/signal/${ticker.toUpperCase()}`);
}


export function fetchNews(ticker: string) {
  return request<NewsResponse>(`/api/news/${ticker.toUpperCase()}`);
}


export function fetchDivergence(ticker: string) {
  return request<DivergenceSnapshot>(`/api/divergence/${ticker.toUpperCase()}`);
}


export function fetchDevToken() {
  return request<{ access_token: string; token_type: string }>("/api/auth/dev-token?subject=frontend-demo");
}


export function analyzePortfolio(token: string, holdings: PortfolioHoldingInput[]) {
  return request<PortfolioResponse>("/api/portfolio/analyze", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ holdings })
  });
}


export type { LivePayload };
