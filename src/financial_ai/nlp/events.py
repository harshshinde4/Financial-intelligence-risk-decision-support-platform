from __future__ import annotations

import re

from financial_ai.nlp.schemas import EventResult

EVENT_RULES: dict[str, tuple[set[str], float]] = {
    "earnings": ({"earnings", "revenue", "profit", "eps", "guidance"}, 0.75),
    "corporate_action": ({"acquisition", "merger", "buyback", "dividend", "split"}, 0.85),
    "regulatory": ({"regulator", "regulatory", "sec", "fine", "penalty", "investigation"}, 0.85),
    "legal": ({"lawsuit", "litigation", "court", "settlement", "fraud"}, 0.90),
    "management": ({"ceo", "cfo", "resigns", "appointed", "executive"}, 0.70),
    "product": ({"launch", "product", "recall", "release", "approval"}, 0.65),
    "macro": ({"inflation", "rates", "fed", "recession", "tariff", "gdp"}, 0.70),
}


def classify_event(text: str) -> EventResult:
    lower = text.lower()
    words = set(re.findall(r"[a-z]+", lower))
    best_type = "general"
    best_terms: list[str] = []
    best_confidence = 0.35
    for event_type, (terms, base_confidence) in EVENT_RULES.items():
        matched = sorted(words & terms)
        if len(matched) > len(best_terms):
            best_type = event_type
            best_terms = matched
            best_confidence = min(0.99, base_confidence + 0.05 * max(0, len(matched) - 1))
    severity = "low"
    if best_type in {"legal", "regulatory", "corporate_action"}:
        severity = "high"
    elif best_type in {"earnings", "management", "macro"}:
        severity = "medium"
    return EventResult(
        event_type=best_type,
        severity=severity,
        confidence=best_confidence,
        matched_terms=best_terms,
    )
