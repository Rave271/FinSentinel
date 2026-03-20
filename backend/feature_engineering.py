#!/usr/bin/env python3
from pathlib import Path

import numpy as np
import pandas as pd

HISTORICAL_DIR = Path(__file__).resolve().parent.parent / "data" / "historical"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "training_features.csv"


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def engineer_ticker_features(csv_path):
    ticker = csv_path.stem.replace("_daily", "")
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.sort_values("date").reset_index(drop=True)
    df["ticker"] = ticker
    df["price_delta_1d"] = df["close"].pct_change(1)
    df["price_delta_5d"] = df["close"].pct_change(5)
    df["rsi_14"] = compute_rsi(df["close"], period=14)
    ma_5 = df["close"].rolling(window=5, min_periods=5).mean()
    ma_20 = df["close"].rolling(window=20, min_periods=20).mean()
    df["ma_cross"] = np.where(ma_5 > ma_20, 1, -1)
    df["price_vs_ma20"] = (df["close"] / ma_20) - 1.0

    volume_mean = df["volume"].rolling(window=20, min_periods=20).mean()
    volume_std = df["volume"].rolling(window=20, min_periods=20).std(ddof=0)
    df["volume_spike_zscore"] = ((df["volume"] - volume_mean) / volume_std.replace(0, np.nan)).fillna(0.0)

    df["sentiment_news"] = 0.0
    df["sentiment_social"] = 0.0
    df["sentiment_divergence"] = 0.0

    next_day_return = df["close"].shift(-1) / df["close"] - 1
    df["label"] = np.select(
        [next_day_return > 0.01, next_day_return < -0.01],
        ["BUY", "SELL"],
        default="HOLD",
    )

    feature_columns = [
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "price_delta_1d",
        "price_delta_5d",
        "rsi_14",
        "ma_cross",
        "price_vs_ma20",
        "volume_spike_zscore",
        "sentiment_news",
        "sentiment_social",
        "sentiment_divergence",
        "label",
    ]

    df = df[feature_columns].dropna(
        subset=["price_delta_1d", "price_delta_5d", "price_vs_ma20"]
    )
    return df


def main():
    csv_paths = sorted(HISTORICAL_DIR.glob("*_daily.csv"))
    if not csv_paths:
        raise FileNotFoundError(f"No historical CSVs found in {HISTORICAL_DIR}")

    frames = [engineer_ticker_features(path) for path in csv_paths]
    combined = pd.concat(frames, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)

    print(f"saved {len(combined)} rows to {OUTPUT_PATH}")
    print("class_distribution")
    print(combined["label"].value_counts().to_string())
    print("sample_rows")
    print(combined.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
