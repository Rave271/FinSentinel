import hashlib
import os
from typing import Optional

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
GROQ_API_KEY = os.environ.get("groq_key")
LLM_SUMMARY_CACHE_TTL = int(os.environ.get("LLM_SUMMARY_CACHE_TTL", "86400"))


class SummaryGenerator:
    def __init__(self):
        if LLM_PROVIDER == "groq":
            if not GROQ_API_KEY:
                raise ValueError("groq_key environment variable is not set")
            from groq import Groq
            self.client = Groq(api_key=GROQ_API_KEY)
            self.model = "llama-3.1-8b-instant"
        else:
            raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

    def generate_summary(
        self, text: str, sentiment_label: str, sentiment_score: float
    ) -> str:
        """Generate a 2-3 sentence summary explaining the sentiment."""
        if not text or not text.strip():
            return ""

        prompt = f"""You are a financial sentiment analyst. Given a financial headline and its sentiment classification, explain in 2-3 sentences why this content carries that sentiment. Focus on: what business/market impact is implied, what drove the sentiment.

Text: "{text}"
Sentiment: {sentiment_label} (confidence: {sentiment_score:.1%})

Explanation:"""

        try:
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7,
            )
            summary = message.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Error generating LLM summary: {e}")
            return ""


_GENERATOR = None


def get_generator() -> SummaryGenerator:
    global _GENERATOR
    if _GENERATOR is None:
        try:
            _GENERATOR = SummaryGenerator()
        except Exception as e:
            print(f"Failed to initialize SummaryGenerator: {e}")
            return None
    return _GENERATOR


def _hash_text(text: str) -> str:
    """Create a cache key from text."""
    return hashlib.sha256(text.encode()).hexdigest()


def get_or_generate_summary(
    text: str, sentiment_label: str, sentiment_score: float, redis_client=None
) -> str:
    """Get cached summary or generate and cache a new one."""
    if not text or not text.strip():
        return ""

    cache_key = f"llm_summary:{_hash_text(text)}"

    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return cached.decode() if isinstance(cached, bytes) else cached
        except Exception as e:
            print(f"Error reading summary cache: {e}")

    generator = get_generator()
    if not generator:
        return ""

    summary = generator.generate_summary(text, sentiment_label, sentiment_score)

    if summary and redis_client:
        try:
            redis_client.setex(cache_key, LLM_SUMMARY_CACHE_TTL, summary)
        except Exception as e:
            print(f"Error writing summary cache: {e}")

    return summary
