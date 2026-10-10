"""Offline validation of a saved financial brief.
Run: python scripts/validate_financial_brief.py AAPL
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "quantitative_analytics",
    "ml_model_comparison",
    "ml_forecast",
    "risk_explainability",
    "risk_assessment",
    "grounded_rag_answer",
)


def validate(report):
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "passed": bool(ok), "detail": str(detail)})

    ticker = report.get("ticker")
    sections = report.get("sections")
    add("Report ticker exists", isinstance(ticker, str) and bool(ticker.strip()), repr(ticker))
    add("Sections object exists", isinstance(sections, dict), type(sections).__name__)
    if not isinstance(sections, dict):
        return checks
    missing = [x for x in REQUIRED if x not in sections]
    add("All expected sections are present", not missing, f"missing={missing or 'none'}")
    statuses = {}
    for name in REQUIRED:
        sec = sections.get(name)
        if not isinstance(sec, dict):
            statuses[name] = "missing_or_invalid"
            add(f"{name}: section shape", False, "missing or not an object")
            continue
        status = sec.get("status")
        statuses[name] = status
        add(
            f"{name}: request status recorded", status in ("success", "error"), f"status={status!r}"
        )
        if status == "success":
            code = sec.get("http_status")
            add(
                f"{name}: HTTP success recorded",
                isinstance(code, int) and 200 <= code < 300,
                f"http_status={code!r}",
            )
        elif status == "error":
            add(
                f"{name}: failure details recorded",
                "error" in sec,
                "error_present=" + str("error" in sec),
            )
    rag = sections.get("grounded_rag_answer", {})
    data = rag.get("data") if isinstance(rag, dict) else None
    if isinstance(data, dict) and rag.get("status") == "success":
        evidence = data.get("evidence") or []
        citations = data.get("citations") or []
        answer = data.get("answer") or ""
        answer_ids = set(re.findall(r"\[(E\d+)\]", answer))
        citation_ids = {
            str(x.get("citation_id"))
            for x in citations
            if isinstance(x, dict) and x.get("citation_id")
        }
        evidence_sources = {
            x.get("source") for x in evidence if isinstance(x, dict) and x.get("source")
        }
        citation_sources = {
            x.get("source") for x in citations if isinstance(x, dict) and x.get("source")
        }
        if data.get("generation_status") == "no_evidence":
            add(
                "RAG no-evidence result has no citations",
                not citations,
                f"citation_count={len(citations)}",
            )
            add(
                "RAG no-evidence result has no evidence",
                not evidence,
                f"evidence_count={len(evidence)}",
            )
        else:
            add(
                "RAG answer citation markers resolve",
                bool(answer_ids) and answer_ids.issubset(citation_ids),
                f"answer_ids={sorted(answer_ids)}, citation_ids={sorted(citation_ids)}",
            )
            add(
                "RAG citation sources exist in evidence",
                bool(citation_sources) and citation_sources.issubset(evidence_sources),
                f"evidence_sources={sorted(evidence_sources)}, "
                f"citation_sources={sorted(citation_sources)}",
            )
    else:
        add(
            "RAG response available for citation validation",
            False,
            "RAG failed or returned non-object payload",
        )
    summary = report.get("summary", {})
    actual = sum(1 for x in statuses.values() if x == "success")
    if isinstance(summary, dict):
        add(
            "Successful endpoint count matches sections",
            summary.get("successful_endpoints") == actual,
            f"recorded={summary.get('successful_endpoints')!r}, actual={actual}",
        )
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", help="Ticker used to create the saved brief")
    args = parser.parse_args()
    safe = args.ticker.strip().upper().replace("/", "_")
    source = ROOT / "data" / "reports" / f"{safe}_financial_brief.json"
    if not source.exists():
        print(f"ERROR: report not found: {source}")
        print(f"Run: python scripts/build_financial_brief.py {args.ticker}")
        return 2
    try:
        report = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: could not read report: {exc}")
        return 2
    checks = validate(report)
    passed = sum(x["passed"] for x in checks)
    failed = len(checks) - passed
    result = {
        "report_path": str(source),
        "ticker": report.get("ticker"),
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(checks), 4) if checks else 0,
        "checks": checks,
    }
    out = ROOT / "data" / "reports" / f"{safe}_validation.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    for item in checks:
        print(f"[{'PASS' if item['passed'] else 'FAIL'}] {item['check']}: {item['detail']}")
    print(f"\nReport validation: {passed}/{len(checks)} checks passed")
    print(f"Validation saved to: {out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
