"""Grounded answer generation via Groq's OpenAI-compatible API."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from typing import Any

SYSTEM_PROMPT = """You are a careful financial risk research assistant.
Answer using only the retrieved evidence supplied by the application.
Do not invent facts, current market conditions, or missing details.
If evidence is insufficient, state that clearly. Do not provide personalized investment
advice, price targets, or guarantees. Cite material factual claims with [E1], [E2], etc.
Never invent citations or sources. Keep the answer concise and acknowledge uncertainty."""

CITATION_PATTERN = re.compile(r"\[(E\d+)\]")


def format_evidence(evidence: Iterable[dict[str, Any]]) -> str:
    blocks = []
    for i, item in enumerate(evidence, start=1):
        passage = str(item.get("text") or "").strip()
        if not passage:
            continue

        metadata = [
            f"{k}={item[k]}"
            for k in ("source", "document_id", "ticker", "published_at")
            if item.get(k) not in (None, "")
        ]
        blocks.append(
            f"[E{i}] ({'; '.join(metadata) if metadata else 'metadata unavailable'})\n{passage}"
        )

    return "\n\n".join(blocks)


def build_user_prompt(question: str, evidence: Iterable[dict[str, Any]]) -> str:
    evidence_text = format_evidence(evidence)
    return (
        f"QUESTION\n{question.strip()}\n\nRETRIEVED EVIDENCE\n"
        f"{evidence_text if evidence_text else '[No evidence retrieved]'}\n\n"
        "Answer only to the extent supported by this evidence. Cite using [E1], [E2], etc. "
        "If evidence is insufficient, say so. Similarity scores are ranking signals, "
        "not probabilities."
    )


def normalize_citations(answer: str, citations: list[dict[str, Any]]) -> str:
    """Ensure every returned citation ID appears in the answer.

    Only citation IDs created from retrieved evidence are allowed.
    A Sources line ensures citation metadata and answer markers stay consistent;
    it does not independently establish semantic support for each claim.
    """
    valid_ids = {str(item["citation_id"]) for item in citations if item.get("citation_id")}

    # Remove citation markers that do not correspond to retrieved evidence.
    def keep_valid_marker(match: re.Match[str]) -> str:
        citation_id = match.group(1)
        return match.group(0) if citation_id in valid_ids else ""

    answer = CITATION_PATTERN.sub(keep_valid_marker, answer).strip()

    present_ids = set(CITATION_PATTERN.findall(answer))
    missing_ids = sorted(valid_ids - present_ids, key=lambda value: int(value[1:]))

    if missing_ids:
        source_line = "Sources: " + ", ".join(f"[{citation_id}]" for citation_id in missing_ids)
        answer = f"{answer}\n\n{source_line}".strip()

    return answer


def generate_grounded_answer(
    question: str,
    evidence: list[dict[str, Any]],
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")

    if not evidence:
        return {
            "answer": (
                "I could not find relevant evidence in the indexed corpus, "
                "so I cannot answer this reliably."
            ),
            "citations": [],
            "model": None,
            "generation_status": "no_evidence",
            "usage": None,
        }

    # Load local .env values for direct calls as well as FastAPI-managed calls.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured in your local .env file.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            'Install the SDK with: python -m pip install "openai>=1.40,<3.0"'
        ) from exc

    chosen_model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    client = OpenAI(
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
    )

    response = client.chat.completions.create(
        model=chosen_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(question, evidence),
            },
        ],
        temperature=0.2,
        max_completion_tokens=400,
    )

    raw_answer = (response.choices[0].message.content or "").strip()

    citations = []
    for i, item in enumerate(evidence, start=1):
        if not str(item.get("text") or "").strip():
            continue

        citations.append(
            {
                "citation_id": f"E{i}",
                "source": item.get("source"),
                "document_id": item.get("document_id"),
                "ticker": item.get("ticker"),
                "published_at": item.get("published_at"),
                "chunk_id": item.get("chunk_id"),
            }
        )

    answer = normalize_citations(raw_answer, citations)

    usage_obj = getattr(response, "usage", None)
    usage = (
        None
        if usage_obj is None
        else {
            "prompt_tokens": getattr(usage_obj, "prompt_tokens", None),
            "completion_tokens": getattr(usage_obj, "completion_tokens", None),
            "total_tokens": getattr(usage_obj, "total_tokens", None),
        }
    )

    return {
        "answer": answer or "The generation model returned an empty answer.",
        "citations": citations,
        "model": chosen_model,
        "generation_status": "generated" if raw_answer else "empty_response",
        "usage": usage,
    }
