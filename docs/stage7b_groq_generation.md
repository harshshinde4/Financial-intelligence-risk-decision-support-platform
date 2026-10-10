# Stage 7B — Grounded answer generation with Groq

This changes only the generation adapter. Document loading, chunking, embeddings, ChromaDB,
retrieval, and metadata filtering remain our local code. Only the final generation request
is sent to Groq.

## 1. Configure .env
Add these lines to your existing `.env`; do not replace other settings:

```dotenv
GROQ_API_KEY=put_your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Keep the key private and ensure `.env` is in `.gitignore`. The model ID is configurable.
Use it only if the Groq console lists it as available to your Free plan; there is no universal
model automatically selected for all API requests.

## 2. Install SDK
With `.venv` activated in the project root:

```powershell
python -m pip install "openai>=1.40,<3.0"
```

## 3. Integrate the route
Keep `/api/v1/rag/retrieve` unchanged. Add `/answer` to the existing
`src/financial_ai/api/routes/rag.py` and reuse the exact retrieval service/function already
used by `/retrieve`; do not create another vector store.

Import:

```python
from financial_ai.rag.generation import generate_grounded_answer
```

The route's core should follow this pattern, adapted to your existing names:

```python
evidence = <the same evidence list returned by your existing retrieval service>
generated = generate_grounded_answer(payload.question, evidence)
return {
    "question": payload.question,
    "ticker_filter": payload.ticker,
    "retrieved_count": len(evidence),
    "evidence": evidence,
    **generated,
}
```

Do not paste the angle-bracket placeholder literally. Follow existing Pydantic conventions and
map missing configuration/provider errors to a controlled HTTP error. Treat rate limits as a
stop condition; do not retry automatically or fall back to paid providers.

## 4. Test
```powershell
python -m pytest tests/test_rag_chunking.py tests/test_rag_embeddings.py tests/test_rag_generation.py -q
```

Then call `POST /api/v1/rag/answer` with:

```json
{
  "question": "What measures should be reviewed when assessing AAPL equity risk?",
  "ticker": "AAPL",
  "top_k": 3
}
```

Expected response includes answer, exact evidence, citations, model ID, generation status,
and token usage when supplied by Groq.

## Zero-cost safeguards
- Stay on Groq Free and verify the selected model is included in your account's free plan.
- Do not upgrade or enable billing.
- Quota/rate-limit errors should pause requests, never trigger paid fallback.
- Context is kept to retrieved passages and output is capped at 400 completion tokens.
