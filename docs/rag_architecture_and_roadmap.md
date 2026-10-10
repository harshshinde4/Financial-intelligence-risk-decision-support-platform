\# RAG Architecture and Development Roadmap



\## 1. Key Components



| Component | Responsibility |

|---|---|

| `documents.py` | Loads local documents and metadata |

| `chunking.py` | Splits documents into overlapping passages |

| `embeddings.py` | Converts text and questions into vectors |

| `vector\_store.py` | Stores vectors and retrieves nearest matches using Chroma |

| `retrieval.py` | Applies retrieval and optional similarity filtering |

| `service.py` | Connects the pipeline components |

| `api/routes/rag.py` | Exposes RAG functionality through FastAPI |



\*\*Current limitation:\*\* The initial chunker uses character-based chunks rather than token-aware chunks. Future improvements include testing chunk sizes, improving chunk boundaries, evaluating retrieval quality, and considering reranking.



\## 2. RAG Pipeline



Question → Embedding model → Question vector → Chroma vector search → Rank matching passages → Return passages and source metadata.



The answer-generation stage uses retrieved evidence to generate a response with source citations. If sufficient evidence is unavailable, the system should abstain rather than invent financial facts.



\## 3. Current Implementation



\- Custom document ingestion, chunking, embeddings, vector storage, retrieval, and metadata filtering.

\- ChromaDB for vector storage and retrieval.

\- Groq API for LLM-based answer generation.

\- Citation normalization and explicit no-evidence handling.

\- Automated tests for retrieval, answer reliability, and API error handling.



\*\*Important distinction:\*\* Generation currently uses Groq, not a locally hosted Qwen model. Local generation would be a separate future implementation.



\## 4. Known Limitations



The initial demonstration uses two synthetic educational documents. It validates the technical pipeline but does not establish production-level financial research quality.



Further evaluation should cover:



\- \*\*Ticker isolation:\*\* Evidence for one ticker must not leak into another ticker's filtered results.

\- \*\*No-evidence behavior:\*\* Unsupported questions should not produce invented financial facts.

\- \*\*Citation integrity:\*\* Every citation must correspond to evidence supplied to the model.

\- \*\*Metadata correctness:\*\* Source, ticker, and publication date must survive indexing and retrieval.

\- \*\*Provider failure handling:\*\* Invalid keys, rate limits, and network errors must be handled predictably.



\## 5. Development Roadmap



1\. \*\*Stage 8 — Evaluation and financial briefs:\*\* Evaluate retrieval, generation reliability, and report validation.

2\. \*\*Stage 9 — Production hardening:\*\* Improve configuration, logging, validation, testing, security, and operational reliability.

3\. \*\*Stage 10 — Deployment:\*\* Prepare containerized deployment, secrets management, monitoring, and reproducible deployment procedures.



Agentic financial workflows and local LLM generation can be introduced as separate enhancements when appropriate.
