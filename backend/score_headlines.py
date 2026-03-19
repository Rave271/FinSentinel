#!/usr/bin/env python3
import csv
import os
from pathlib import Path

from app.sentiment import score_texts

INPUT_COLUMNS = ["id", "headline", "source", "published_at", "url"]
OUTPUT_COLUMNS = [
    "headline",
    "source",
    "published_at",
    "sentiment_label",
    "sentiment_score",
]


def load_news_rows(path: Path):
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for raw_row in reader:
            if not raw_row:
                continue
            if raw_row[0].strip().lower() == "id":
                continue
            if len(raw_row) < len(INPUT_COLUMNS):
                continue
            rows.append(
                {
                    "id": raw_row[0],
                    "headline": raw_row[1],
                    "source": raw_row[2],
                    "published_at": raw_row[3],
                    "url": raw_row[4],
                }
            )
    return rows


def main():
    repo_root = Path(__file__).resolve().parent.parent
    input_path = repo_root / "data" / "news_headlines.csv"
    output_path = repo_root / "data" / "scored_headlines.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")

    rows = load_news_rows(input_path)
    scores = score_texts([row["headline"] for row in rows])

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row, score in zip(rows, scores):
            writer.writerow(
                {
                    "headline": row["headline"],
                    "source": row["source"],
                    "published_at": row["published_at"],
                    "sentiment_label": score["sentiment_label"],
                    "sentiment_score": score["sentiment_score"],
                }
            )

    print(f"Scored {len(rows)} headlines to {output_path}")


if __name__ == "__main__":
    main()
