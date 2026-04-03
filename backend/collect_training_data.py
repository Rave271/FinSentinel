#!/usr/bin/env python3
import csv
import json
import os
import time
import datetime as dt
import urllib.parse
import urllib.request
from pathlib import Path

from app.universe import NIFTY50_SYMBOLS


TICKERS = NIFTY50_SYMBOLS

REQUEST_DELAY_SECONDS = 12
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "historical"
DEFAULT_OUTPUTSIZE = os.environ.get("ALPHA_VANTAGE_OUTPUTSIZE", "compact")
MARKET_SUFFIX = ".BSE"
YAHOO_MARKET_SUFFIX = ".NS"
YAHOO_RANGE = os.environ.get("YAHOO_RANGE", "2y")
YAHOO_INTERVAL = os.environ.get("YAHOO_INTERVAL", "1d")


def load_env_file(path):
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env


def fetch_daily_series(api_key, ticker, outputsize="full"):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": f"{ticker}{MARKET_SUFFIX}",
        "outputsize": outputsize,
        "apikey": api_key,
    }
    url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    return payload


def fetch_yahoo_daily_series(ticker):
    symbol = f"{ticker}{YAHOO_MARKET_SUFFIX}"
    encoded_symbol = urllib.parse.quote(symbol, safe="")
    params = urllib.parse.urlencode(
        {
            "range": YAHOO_RANGE,
            "interval": YAHOO_INTERVAL,
            "includePrePost": "false",
            "events": "div,splits",
        }
    )
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_symbol}?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def parse_yahoo_chart_payload(payload):
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise RuntimeError(f"Yahoo Finance error: {chart['error']}")

    results = chart.get("result") or []
    if not results:
        raise RuntimeError(f"Yahoo Finance returned no result: {payload}")

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})
    quotes = (indicators.get("quote") or [{}])[0]
    opens = quotes.get("open") or []
    highs = quotes.get("high") or []
    lows = quotes.get("low") or []
    closes = quotes.get("close") or []
    volumes = quotes.get("volume") or []

    series = {}
    for index, timestamp in enumerate(timestamps):
        if index >= len(closes):
            continue
        if None in (
            opens[index] if index < len(opens) else None,
            highs[index] if index < len(highs) else None,
            lows[index] if index < len(lows) else None,
            closes[index] if index < len(closes) else None,
            volumes[index] if index < len(volumes) else None,
        ):
            continue
        date_value = dt.datetime.fromtimestamp(int(timestamp), tz=dt.timezone.utc).date().isoformat()
        series[date_value] = {
            "1. open": opens[index],
            "2. high": highs[index],
            "3. low": lows[index],
            "4. close": closes[index],
            "5. volume": volumes[index],
        }

    if not series:
        raise RuntimeError("Yahoo Finance payload contained no valid OHLCV rows")
    return series


def write_daily_csv(ticker, series):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{ticker}_daily.csv"
    rows = sorted(series.items(), key=lambda item: item[0])
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "open", "high", "low", "close", "volume"])
        for date, values in rows:
            writer.writerow(
                [
                    date,
                    values.get("1. open"),
                    values.get("2. high"),
                    values.get("3. low"),
                    values.get("4. close"),
                    values.get("5. volume"),
                ]
            )
    return output_path


def output_path_for_ticker(ticker):
    return OUTPUT_DIR / f"{ticker}_daily.csv"


def main():
    repo_root = Path(__file__).resolve().parent.parent
    env = load_env_file(repo_root / ".env")
    api_key = env.get("ALPHA_VANTAGE_KEY") or os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key:
        raise RuntimeError("ALPHA_VANTAGE_KEY not found in .env or environment")

    tickers_to_fetch = [ticker for ticker in TICKERS if not output_path_for_ticker(ticker).exists()]
    if not tickers_to_fetch:
        print("all historical CSVs already exist")
        return

    print(f"fetching {len(tickers_to_fetch)} missing tickers")
    for index, ticker in enumerate(tickers_to_fetch):
        print(f"[{index + 1}/{len(tickers_to_fetch)}] fetching {ticker}")
        series = None
        alpha_payload = fetch_daily_series(api_key, ticker, outputsize=DEFAULT_OUTPUTSIZE)
        if "Error Message" in alpha_payload:
            print(f"Alpha Vantage error for {ticker}; trying Yahoo Finance fallback")
        elif "Note" in alpha_payload or "Information" in alpha_payload:
            print(f"Alpha Vantage rate limit hit for {ticker}; trying Yahoo Finance fallback")
        else:
            series = alpha_payload.get("Time Series (Daily)")

        if not series:
            yahoo_payload = fetch_yahoo_daily_series(ticker)
            series = parse_yahoo_chart_payload(yahoo_payload)
            print(f"Yahoo Finance fallback succeeded for {ticker}")

        output_path = write_daily_csv(ticker, series)
        print(f"saved {ticker} -> {output_path}")

        if index < len(tickers_to_fetch) - 1:
            print(f"sleeping {REQUEST_DELAY_SECONDS}s to respect Alpha Vantage free-tier limits")
            time.sleep(REQUEST_DELAY_SECONDS)


if __name__ == "__main__":
    main()
