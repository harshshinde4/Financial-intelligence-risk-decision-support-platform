from financial_ai.rag.embeddings import HashingEmbedder


def test_hashing_embedder_is_deterministic():
    e = HashingEmbedder(32)
    assert e.embed_query("risk volatility") == e.embed_query("risk volatility")
    v = e.embed_query("risk volatility")
    assert abs(sum(x * x for x in v) ** 0.5 - 1) < 1e-8


def test_empty_embedding():
    assert all(x == 0 for x in HashingEmbedder(16).embed_query(""))
