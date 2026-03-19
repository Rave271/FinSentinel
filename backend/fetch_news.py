#!/usr/bin/env python3
import os
import json
import csv
import urllib.parse
import urllib.request
from datetime import datetime


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


def fetch_news(api_key, query="finance OR market OR stocks", page_size=20):
    base = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "pageSize": str(page_size),
        "sortBy": "publishedAt",
        "apiKey": api_key,
    }
    url = base + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.load(resp)
    return data


def write_csv(rows, out_path):
    exists = os.path.exists(out_path)
    with open(out_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["id", "headline", "source", "publishedAt", "url"])
        for r in rows:
            writer.writerow([r["id"], r["headline"], r.get("source", ""), r.get("publishedAt", ""), r.get("url", "")])


def main():
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(repo_root, ".env")
    env = load_env_file(env_path)
    news_key = env.get("NEWS_API_KEY") or os.environ.get("NEWS_API_KEY")
    if not news_key:
        print("NEWS_API_KEY not found in .env or environment; aborting.")
        return 2

    print("Fetching news from NewsAPI...")
    data = fetch_news(news_key)
    if data.get("status") != "ok":
        print("NewsAPI error:", data)
        return 3

    articles = data.get("articles", [])
    out_path = os.path.join(repo_root, "data", "news_headlines.csv")

    # determine starting id
    start_id = 1
    if os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                if len(lines) > 1:
                    last = lines[-1].split(",", 1)[0]
                    start_id = int(last) + 1
        except Exception:
            start_id = 1

    rows = []
    for i, a in enumerate(articles, start=start_id):
        title = a.get("title") or a.get("description") or ""
        source = (a.get("source") or {}).get("name")
        published = a.get("publishedAt")
        url = a.get("url")
        rows.append({"id": i, "headline": title, "source": source, "publishedAt": published, "url": url})

    write_csv(rows, out_path)
    print(f"Wrote {len(rows)} articles to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
