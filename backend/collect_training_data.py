#!/usr/bin/env python3
import csv
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

TICKERS = [
    "RELIANCE",
    "INFY",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "WIPRO",
    "AXISBANK",
    "SBIN",
    "LT",
    "BAJFINANCE",
]

REQUEST_DELAY_SECONDS = 12
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "historical"
DEFAULT_OUTPUTSIZE = os.environ.get("ALPHA_VANTAGE_OUTPUTSIZE", "compact")
MARKET_SUFFIX = ".BSE"


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
        payload = fetch_daily_series(api_key, ticker, outputsize=DEFAULT_OUTPUTSIZE)
        if "Error Message" in payload:
            raise RuntimeError(f"Alpha Vantage error for {ticker}: {payload['Error Message']}")
        if "Note" in payload:
            raise RuntimeError(f"Alpha Vantage rate limit note for {ticker}: {payload['Note']}")
        if "Information" in payload:
            raise RuntimeError(f"Alpha Vantage info for {ticker}: {payload['Information']}")

        series = payload.get("Time Series (Daily)")
        if not series:
            raise RuntimeError(f"Missing daily series for {ticker}: {payload}")

        output_path = write_daily_csv(ticker, series)
        print(f"saved {ticker} -> {output_path}")

        if index < len(tickers_to_fetch) - 1:
            print(f"sleeping {REQUEST_DELAY_SECONDS}s to respect Alpha Vantage free-tier limits")
            time.sleep(REQUEST_DELAY_SECONDS)


if __name__ == "__main__":
    main()
