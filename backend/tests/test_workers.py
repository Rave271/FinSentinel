from fakeredis import FakeRedis

from app.workers import price_worker, news_worker, social_worker
from app import sentiment


def test_push_price_event_creates_stream_entry(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(price_worker, 'redis', r)
    row = {'symbol': 'TEST', 'price': '123.45', 'volume': '1000', 'timestamp': '2026-03-20T00:00:00Z'}
    price_worker.push_price_event(row, redis_client=r)
    assert r.xlen('stream:price') >= 1


def test_push_article_deduplicates(monkeypatch, tmp_path):
    r = FakeRedis()
    monkeypatch.setattr(news_worker, 'redis', r)
    article = {
        'ticker': 'INFY',
        'headline': 'Hello World',
        'source': 'test',
        'published_at': '2026-03-20T00:00:00Z',
        'sentiment_label': 'neutral',
        'sentiment_score': 0.0,
        'ts': '2026-03-20T00:00:30Z',
        'url': 'http://example.com/a',
    }
    news_worker.push_article(article, redis_client=r)
    news_worker.push_article(article, redis_client=r)
    assert r.xlen('news:stream') == 1


def test_enrich_articles_with_sentiment(monkeypatch):
    monkeypatch.setattr(
        news_worker.sentiment,
        "score_texts",
        lambda texts: [{"sentiment_label": "positive", "sentiment_score": 0.75} for _ in texts],
    )
    rows = [
        {
            "headline": "INFY beats estimates",
            "source": "test",
            "publishedAt": "2026-03-20T00:00:00Z",
            "url": "http://example.com/1",
        }
    ]
    enriched = news_worker.enrich_articles_with_sentiment(rows)
    assert enriched[0]["ticker"] == "INFY"
    assert enriched[0]["sentiment_label"] == "positive"
    assert enriched[0]["sentiment_score"] == 0.75


def test_push_social_event_creates_stream_entry(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(social_worker, "redis", r)
    social_worker.push_event(
        ticker="INFY",
        text="INFY stock climbs | Positive analyst outlook",
        source="google-news-rss",
        ts="2026-03-20T00:00:00Z",
        sentiment_label="positive",
        sentiment_score=0.88,
        redis_client=r,
    )
    assert r.xlen("social:stream") == 1


def test_fetch_ticker_news_parses_title_and_summary(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(social_worker, "redis", r)
    monkeypatch.setattr(
        social_worker.sentiment,
        "score_texts",
        lambda texts: [{"sentiment_label": "positive", "sentiment_score": 0.91} for _ in texts],
    )

    class FakeParser:
        @staticmethod
        def parse(url):
            return type(
                "FakeFeed",
                (),
                {
                    "bozo": 0,
                    "entries": [
                        {
                            "title": "INFY stock jumps",
                            "summary": "Analysts expect stronger quarter.",
                            "published": "2026-03-20T00:00:00Z",
                        }
                    ],
                },
            )()

    social_worker.fetch_ticker_news("INFY", redis_client=r, parser=FakeParser())
    entries = r.xrange("social:stream")
    assert len(entries) == 1
    fields = entries[0][1]
    assert fields[b"ticker"] == b"INFY"
    assert b"INFY stock jumps" in fields[b"text"]
    assert b"Analysts expect stronger quarter." in fields[b"text"]
    assert fields[b"source"] == b"google-news-rss"
    assert fields[b"sentiment_label"] == b"positive"
    assert fields[b"sentiment_score"] == b"0.91"


def test_compute_ewma_score_returns_smoothed_value():
    value = sentiment.compute_ewma_score(
        "INFY",
        [0.2, 0.8],
        ["2026-03-20T00:00:00Z", "2026-03-20T00:30:00Z"],
    )
    assert 0.49 < value < 0.51
