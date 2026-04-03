import asyncio

from fakeredis import FakeRedis

from app import explainability


def _sample_features():
    return explainability.load_latest_training_row("INFY")


def test_build_signal_explanation_returns_ranked_payload():
    explanation = explainability.build_signal_explanation("INFY", _sample_features())

    assert explanation["ticker"] == "INFY"
    assert explanation["signal"]["label"] in {"BUY", "HOLD", "SELL"}
    assert explanation["signal"]["confidence"] >= 0.0
    assert explanation["model"]["feature_count"] == 9
    assert len(explanation["top_factors"]) == 3
    assert explanation["narrative"]["headline"]
    assert explanation["narrative"]["summary"]
    assert len(explanation["narrative"]["details"]) == 3

    magnitudes = [abs(item["shap_value"]) for item in explanation["top_factors"]]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_render_explanation_text_mentions_support_and_drag():
    narrative = explainability.render_explanation_text(
        signal_label="BUY",
        confidence=0.8123,
        top_factors=[
            {"label": "news sentiment", "display_value": "+0.640", "shap_value": 0.42, "effect": "supports"},
            {"label": "social sentiment", "display_value": "+0.410", "shap_value": 0.31, "effect": "supports"},
            {"label": "RSI momentum", "display_value": "78.5", "shap_value": -0.19, "effect": "tempers"},
        ],
    )

    assert "BUY" in narrative["headline"]
    assert "Strongest support comes from news sentiment, social sentiment." in narrative["summary"]
    assert "Main drag comes from RSI momentum." in narrative["summary"]
    assert len(narrative["details"]) == 3


def test_cache_signal_explanation_round_trip():
    r = FakeRedis()
    payload = {"ticker": "INFY", "signal": {"label": "BUY"}}

    assert explainability.cache_signal_explanation("INFY", payload, redis_client=r)
    cached = explainability.get_cached_signal_explanation("INFY", redis_client=r)

    assert cached == payload
    assert 0 < r.ttl(explainability.explanation_cache_key("INFY")) <= explainability.EXPLANATION_TTL_SECONDS


def test_precompute_signal_explanation_populates_cache():
    r = FakeRedis()
    result = asyncio.run(
        explainability.precompute_signal_explanation("INFY", _sample_features(), redis_client=r)
    )

    cached = explainability.get_cached_signal_explanation("INFY", redis_client=r)
    assert cached is not None
    assert cached["signal"]["label"] == result["signal"]["label"]
