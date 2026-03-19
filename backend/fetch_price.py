#!/usr/bin/env python3
import os
import json
import urllib.parse
import urllib.request
import sys
import csv


def load_env_file(path):
    env = {}
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env


def fetch_global_quote(api_key, symbol):
    base = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    }
    url = base + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.load(resp)
    return data


def write_csv(row, out_path):
    exists = os.path.exists(out_path)
    with open(out_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["symbol", "price", "volume", "timestamp"])
        writer.writerow([row.get("symbol"), row.get("price"), row.get("volume"), row.get("timestamp")])


def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(repo_root, ".env")
    env = load_env_file(env_path)
    av_key = env.get("ALPHA_VANTAGE_KEY") or os.environ.get("ALPHA_VANTAGE_KEY")
    if not av_key:
        print("ALPHA_VANTAGE_KEY not found in .env or environment; aborting.")
        return 2

    print(f"Fetching price for {symbol} from Alpha Vantage...")
    data = fetch_global_quote(av_key, symbol)
    quote = data.get("Global Quote") or {}
    price = quote.get("05. price")
    volume = quote.get("06. volume")
    timestamp = quote.get("07. latest trading day")

    out = {"symbol": symbol, "price": price, "volume": volume, "timestamp": timestamp}
    out_path = os.path.join(repo_root, "data", "price_quotes.csv")
    write_csv(out, out_path)
    print(f"Wrote quote for {symbol} to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
