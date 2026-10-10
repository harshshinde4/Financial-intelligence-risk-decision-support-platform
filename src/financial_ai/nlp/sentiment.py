from __future__ import annotations

from functools import lru_cache

from financial_ai.nlp.schemas import SentimentResult


@lru_cache(maxsize=1)
def _finbert():
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        top_k=None,
        truncation=True,
    )


def analyze_sentiment(text: str, use_finbert: bool = True) -> SentimentResult:
    text = text.strip()
    if not text:
        return SentimentResult(label="neutral", score=1.0, positive=0.0, negative=0.0, neutral=1.0)

    if use_finbert:
        try:
            outputs = _finbert()(text[:4000])[0]
            scores = {str(x["label"]).lower(): float(x["score"]) for x in outputs}
            positive = scores.get("positive", 0.0)
            negative = scores.get("negative", 0.0)
            neutral = scores.get("neutral", 0.0)
            label = max(scores, key=scores.get)
            return SentimentResult(
                label=label,
                score=scores[label],
                positive=positive,
                negative=negative,
                neutral=neutral,
            )
        except Exception:
            # Deterministic fallback keeps ingestion usable if the model cannot be downloaded.
            pass

    positive_terms = {"beat", "growth", "profit", "upgrade", "strong", "surge", "record"}
    negative_terms = {"miss", "loss", "downgrade", "decline", "weak", "lawsuit", "cut"}
    tokens = {word.strip('.,:;!?()[]{}"').lower() for word in text.split()}
    p = len(tokens & positive_terms)
    n = len(tokens & negative_terms)
    if p == n:
        return SentimentResult(label="neutral", score=1.0, positive=0.0, negative=0.0, neutral=1.0)
    label = "positive" if p > n else "negative"
    score = max(p, n) / max(p + n, 1)
    return SentimentResult(
        label=label,
        score=float(score),
        positive=float(p / max(p + n, 1)),
        negative=float(n / max(p + n, 1)),
        neutral=0.0,
    )
