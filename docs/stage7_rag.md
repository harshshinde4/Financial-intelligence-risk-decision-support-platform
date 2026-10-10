# Stage 7 — Financial RAG from Scratch

This stage implements retrieval, not generation, so you can inspect retrieval quality before an LLM produces fluent but potentially unsupported answers.

Pipeline: local document loading -> chunking -> metadata -> local sentence-transformer embeddings -> persistent Chroma vector store -> question embedding -> vector retrieval -> inspectable evidence.

## Concepts
- **Chunking:** splits long documents into searchable units; this baseline uses character windows.
- **Overlap:** preserves text crossing chunk boundaries, but excessive overlap duplicates results.
- **Embeddings:** dense vectors that place semantically related text near each other.
- **Vector store:** stores vectors, chunks and metadata persistently.
- **Cosine similarity:** Chroma uses cosine distance. `1 - distance` is a ranking score, not a probability.
- **Metadata:** source/ticker/date allows filtering and traceability.
- **Grounding:** the future generation step will cite retrieved sources and admit when evidence is missing.

## Additive patch
This ZIP does not replace `main.py`, migrations, `.env`, or existing Stage 1–6 files. Add router registration manually:
`from financial_ai.api.routes.rag import router as rag_router`
and alongside existing registrations:
`app.include_router(rag_router, prefix=settings.api_v1_prefix)`

The `[llm]` optional dependencies should include `sentence-transformers>=3.0,<6.0` and `chromadb>=0.5,<2.0`. Install with:
`python -m pip install -e ".[dev,ml,nlp,llm]"`

## Try it
1. Run `python -m pytest`.
2. Start `uvicorn financial_ai.api.main:app --reload`.
3. Open `/docs`.
4. `POST /api/v1/rag/index` body: `{"chunk_size":900,"overlap":150}`.
5. `POST /api/v1/rag/retrieve` body: `{"question":"What measures should be reviewed when assessing equity risk?","ticker":null,"top_k":3}`.

The first indexing call may download/cache `sentence-transformers/all-MiniLM-L6-v2`. Allow network access and time for the first download.

Limitations: .txt/.md only, character-based chunking, no PDF extraction, reranker or LLM generation yet. Demo documents are synthetic and must not be treated as real financial research.
