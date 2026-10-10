"""Smoke-test RAG answer grounding and citation consistency.

This calls the local /rag/answer endpoint. The AAPL case may consume a small
amount of Groq usage; the TSLA case should abstain before generation if no
TSLA-tagged evidence exists.
Run from the project root:
    python scripts/evaluate_rag_answers.py
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "http://127.0.0.1:8000/api/v1/rag/answer"


def post_json(payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach {ENDPOINT}. Is the FastAPI server running? Details: {exc}"
        ) from exc


def check_aapl() -> list[tuple[str, bool, str]]:
    result = post_json(
        {
            "question": "What measures should be reviewed when assessing AAPL equity risk?",
            "ticker": "AAPL",
            "top_k": 3,
        }
    )
    evidence = result.get("evidence") or []
    answer = result.get("answer") or ""
    citations = result.get("citations") or []
    status = result.get("generation_status")
    checks: list[tuple[str, bool, str]] = []

    checks.append(("AAPL evidence returned", bool(evidence), f"count={len(evidence)}"))
    checks.append(
        (
            "Answer generated",
            status == "generated" and bool(answer.strip()),
            f"generation_status={status!r}",
        )
    )

    answer_ids = set(re.findall(r"\[(E\d+)\]", answer))
    citation_ids = {str(item.get("citation_id")) for item in citations if item.get("citation_id")}
    checks.append(
        (
            "Answer citation markers map to returned citations",
            bool(answer_ids) and answer_ids.issubset(citation_ids),
            f"answer_ids={sorted(answer_ids)}, citation_ids={sorted(citation_ids)}",
        )
    )

    evidence_sources = {item.get("source") for item in evidence if item.get("source")}
    citation_sources = {item.get("source") for item in citations if item.get("source")}
    checks.append(
        (
            "Citation sources come from retrieved evidence",
            bool(citation_sources) and citation_sources.issubset(evidence_sources),
            f"evidence_sources={sorted(evidence_sources)}, "
            f"citation_sources={sorted(citation_sources)}",
        )
    )

    answer_lower = answer.lower()
    expected_terms = [
        "realized volatility",
        "maximum drawdown",
        "downside tail risk",
        "earnings",
        "regulatory",
        "forward guidance",
    ]
    missing = [term for term in expected_terms if term not in answer_lower]
    checks.append(
        (
            "Answer covers key concepts from the demo risk note",
            not missing,
            "missing terms=" + (", ".join(missing) if missing else "none"),
        )
    )
    return checks


def check_unknown_ticker() -> list[tuple[str, bool, str]]:
    result = post_json(
        {
            "question": "What does the internal risk note say about TSLA?",
            "ticker": "TSLA",
            "top_k": 3,
        }
    )
    evidence = result.get("evidence") or []
    status = result.get("generation_status")
    answer = result.get("answer") or ""
    citations = result.get("citations") or []
    checks = [
        ("Unknown ticker returns no evidence", len(evidence) == 0, f"count={len(evidence)}"),
        (
            "No-evidence case abstains",
            status == "no_evidence" and "cannot answer" in answer.lower(),
            f"generation_status={status!r}, answer={answer!r}",
        ),
        ("No-evidence case has no citations", len(citations) == 0, f"citations={len(citations)}"),
    ]
    return checks


def main() -> int:
    all_checks: list[tuple[str, bool, str]] = []
    for section, fn in (
        ("AAPL grounded answer", check_aapl),
        ("Unknown ticker abstention", check_unknown_ticker),
    ):
        print(f"\n## {section}")
        try:
            checks = fn()
        except Exception as exc:
            checks = [(f"{section} request completed", False, str(exc))]
        for name, passed, detail in checks:
            print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
            all_checks.append((name, passed, detail))

    passed_count = sum(1 for _, passed, _ in all_checks if passed)
    total = len(all_checks)
    report = {
        "endpoint": ENDPOINT,
        "total_checks": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": round(passed_count / total, 4) if total else 0,
        "checks": [
            {"check": name, "passed": passed, "detail": detail}
            for name, passed, detail in all_checks
        ],
    }
    report_path = ROOT / "data" / "rag" / "evaluation" / "latest_answer_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nAnswer reliability checks: {passed_count}/{total} passed")
    print(f"Report saved to: {report_path}")
    return 0 if passed_count == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
