import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FinancialDocument:
    document_id: str
    text: str
    source: str
    ticker: str | None = None
    published_at: str | None = None
    metadata: dict[str, Any] | None = None


def load_documents(directory: str | Path) -> list[FinancialDocument]:
    root = Path(directory)
    if not root.exists():
        return []
    docs = []
    for path in sorted([*root.glob("*.txt"), *root.glob("*.md")]):
        sidecar = path.with_suffix(".json")
        meta = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
        content = path.read_text(encoding="utf-8").strip()
        if content:
            docs.append(
                FinancialDocument(
                    path.stem,
                    content,
                    str(meta.get("source", path.name)),
                    meta.get("ticker"),
                    meta.get("published_at"),
                    {
                        k: v
                        for k, v in meta.items()
                        if k not in {"source", "ticker", "published_at"}
                    },
                )
            )
    return docs
