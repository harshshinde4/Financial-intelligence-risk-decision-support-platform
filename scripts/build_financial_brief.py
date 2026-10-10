"""Build a deterministic multi-endpoint financial intelligence brief.

This orchestrator calls existing local API endpoints and stores their raw JSON
responses together. It does not ask an LLM to calculate, alter, or synthesize
financial metrics. Run from the project root with FastAPI running:
    python scripts/build_financial_brief.py AAPL
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8000"


def request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
            return {
                "status": "success",
                "http_status": response.status,
                "data": json.loads(body) if body else None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            details = json.loads(body)
        except json.JSONDecodeError:
            details = body
        return {
            "status": "error",
            "http_status": exc.code,
            "error": details,
        }
    except (urllib.error.URLError, TimeoutError) as exc:
        return {"status": "error", "error": str(exc)}
    except json.JSONDecodeError as exc:
        return {"status": "error", "error": f"Endpoint returned invalid JSON: {exc}"}


def build_brief(ticker: str, top_k: int = 3) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    # Endpoints are intentionally queried independently: one failure must not
    # prevent the remaining components from being captured.
    endpoints: dict[str, tuple[str, str, dict[str, Any] | None]] = {
        "quantitative_analytics": ("GET", f"/api/v1/analytics/{ticker}/summary", None),
        "ml_model_comparison": ("GET", f"/api/v1/ml/{ticker}/compare", None),
        "ml_forecast": ("GET", f"/api/v1/ml/{ticker}/forecast", None),
        "risk_explainability": ("GET", f"/api/v1/intelligence/{ticker}/explain", None),
        "risk_assessment": ("GET", f"/api/v1/intelligence/{ticker}/risk", None),
        "grounded_rag_answer": (
            "POST",
            "/api/v1/rag/answer",
            {
                "question": (
                    f"Summarize the available risk considerations and limitations "
                    f"for {ticker} using only retrieved evidence."
                ),
                "ticker": ticker,
                "top_k": top_k,
            },
        ),
    }

    results: dict[str, Any] = {}
    for name, (method, path, payload) in endpoints.items():
        results[name] = {
            "method": method,
            "path": path,
            **request_json(method, path, payload),
        }

    success_count = sum(1 for item in results.values() if item["status"] == "success")
    failed = [name for name, item in results.items() if item["status"] != "success"]
    return {
        "report_type": "deterministic_financial_intelligence_brief",
        "ticker": ticker,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "disclaimer": (
            "This report bundles outputs from separate project endpoints. "
            "Endpoint outputs are not independently verified investment research, "
            "forecasts are uncertain, and this report is not investment advice. "
            "Review each section's status and source metadata before relying on it."
        ),
        "summary": {
            "endpoint_count": len(results),
            "successful_endpoints": success_count,
            "failed_endpoints": len(failed),
            "failed_sections": failed,
        },
        "sections": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticker", help="Ticker symbol, e.g. AAPL or RELIANCE.NS")
    parser.add_argument("--top-k", type=int, default=3, help="RAG evidence count (1–10)")
    args = parser.parse_args()
    ticker = args.ticker.strip().upper()
    if not ticker or len(ticker) > 30:
        parser.error("ticker must contain 1–30 characters")
    if not 1 <= args.top_k <= 10:
        parser.error("--top-k must be between 1 and 10")

    report = build_brief(ticker, args.top_k)
    out_dir = ROOT / "data" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{ticker.replace('/', '_')}_financial_brief.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Financial brief created for {ticker}")
    print(
        f"Endpoint results: {report['summary']['successful_endpoints']}/"
        f"{report['summary']['endpoint_count']} succeeded"
    )
    if report["summary"]["failed_sections"]:
        print("Failed sections:")
        for name in report["summary"]["failed_sections"]:
            print(f" - {name}: {report['sections'][name].get('error')}")
    print(f"Report saved to: {output_path}")
    return 0 if not report["summary"]["failed_sections"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
