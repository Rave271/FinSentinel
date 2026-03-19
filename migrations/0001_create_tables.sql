-- Phase 1 initial schema for FinSentinel
CREATE TABLE IF NOT EXISTS headlines (
  id SERIAL PRIMARY KEY,
  external_id TEXT,
  headline TEXT NOT NULL,
  source TEXT,
  published_at TIMESTAMP,
  sentiment_score REAL
);

CREATE TABLE IF NOT EXISTS news_articles (
  id SERIAL PRIMARY KEY,
  external_id TEXT,
  title TEXT NOT NULL,
  source TEXT,
  url TEXT,
  published_at TIMESTAMP,
  sentiment_score REAL
);

CREATE TABLE IF NOT EXISTS price_quotes (
  id SERIAL PRIMARY KEY,
  symbol TEXT NOT NULL,
  price NUMERIC,
  volume BIGINT,
  timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS social_posts (
  id SERIAL PRIMARY KEY,
  external_id TEXT,
  text TEXT NOT NULL,
  source TEXT,
  published_at TIMESTAMP,
  sentiment_score REAL
);
