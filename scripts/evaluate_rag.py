"""Low-cost retrieval evaluation against the local FastAPI RAG endpoint.
Run from the project root with the API server running:
    python scripts/evaluate_rag.py
This script calls retrieval only; it does not call Groq or generate answers.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "data" / "rag" / "evaluation" / "questions.json"
ENDPOINT = "http://127.0.0.1:8000/api/v1/rag/retrieve"


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach {url}. Is the FastAPI server running? Details: {exc}"
        ) from exc


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = post_json(
        ENDPOINT,
        {
            "question": case["question"],
            "ticker": case.get("ticker"),
            "top_k": case.get("top_k", 3),
        },
    )
    evidence = result.get("evidence") or []
    expected_empty = bool(case.get("expect_empty", False))
    expected_source = case.get("expected_source")
    expected_ticker = case.get("expected_ticker")

    if expected_empty:
        passed = len(evidence) == 0
        reason = "correctly returned no evidence" if passed else "expected no evidence"
    else:
        source_hit = expected_source is None or any(
            item.get("source") == expected_source for item in evidence
        )
        ticker_hit = expected_ticker is None or any(
            str(item.get("ticker") or "").upper() == expected_ticker.upper() for item in evidence
        )
        passed = bool(evidence) and source_hit and ticker_hit
        reasons = []
        if not evidence:
            reasons.append("no evidence returned")
        if evidence and not source_hit:
            reasons.append(f"expected source {expected_source!r} not retrieved")
        if evidence and not ticker_hit:
            reasons.append(f"expected ticker {expected_ticker!r} not retrieved")
        reason = "expected evidence retrieved" if passed else "; ".join(reasons)

    return {
        "id": case["id"],
        "passed": passed,
        "reason": reason,
        "retrieved_count": len(evidence),
        "sources": sorted({str(x.get("source")) for x in evidence if x.get("source")}),
        "tickers": sorted({str(x.get("ticker")) for x in evidence if x.get("ticker")}),
    }


def main() -> int:
    if not DATASET_PATH.exists():
        print(f"Evaluation dataset not found: {DATASET_PATH}", file=sys.stderr)
        return 2
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        print("Dataset must be a non-empty JSON list.", file=sys.stderr)
        return 2

    results = []
    for case in cases:
        try:
            row = evaluate_case(case)
        except Exception as exc:
            row = {
                "id": case.get("id", "<unknown>"),
                "passed": False,
                "reason": f"evaluation error: {exc}",
                "retrieved_count": 0,
                "sources": [],
                "tickers": [],
            }
        results.append(row)
        print(
            f"[{'PASS' if row['passed'] else 'FAIL'}] {row['id']}: {row['reason']} "
            f"(retrieved={row['retrieved_count']}, sources={row['sources']}, "
            f"tickers={row['tickers']})"
        )

    passed = sum(1 for row in results if row["passed"])
    report = {
        "endpoint": ENDPOINT,
        "total_cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": round(passed / len(results), 4),
        "results": results,
    }
    report_path = ROOT / "data" / "rag" / "evaluation" / "latest_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nRetrieval evaluation: {passed}/{len(results)} passed ({passed / len(results):.1%})")
    print(f"Report saved to: {report_path}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
