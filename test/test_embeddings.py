import pytest
from embeddings import (
    serialize_embedding, deserialize_embedding, estimate_tokens,
    batch_by_tokens, EMBEDDING_DIM, MAX_TOKENS_PER_REQUEST
)


def test_serialize_deserialize_roundtrip():
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    blob = serialize_embedding(embedding)
    result = deserialize_embedding(blob)
    
    assert len(result) == len(embedding)
    for a, b in zip(result, embedding):
        assert abs(a - b) < 1e-6


def test_serialize_embedding_size():
    embedding = [0.0] * 10
    blob = serialize_embedding(embedding)
    assert len(blob) == 10 * 4


def test_deserialize_embedding_full_dim():
    embedding = [float(i) / EMBEDDING_DIM for i in range(EMBEDDING_DIM)]
    blob = serialize_embedding(embedding)
    result = deserialize_embedding(blob)
    assert len(result) == EMBEDDING_DIM


def test_embedding_dim_constant():
    assert EMBEDDING_DIM == 1536


def test_max_tokens_constant():
    assert MAX_TOKENS_PER_REQUEST == 250000


def test_estimate_tokens():
    assert estimate_tokens("12345678") == 2
    assert estimate_tokens("") == 0


def test_batch_by_tokens_single_batch():
    texts = ["short", "texts", "here"]
    batches = batch_by_tokens(texts)
    assert len(batches) == 1
    assert batches[0] == texts


def test_batch_by_tokens_splits_large():
    texts = ["x" * 1000 for _ in range(10)]
    batches = batch_by_tokens(texts, max_tokens=500)
    assert len(batches) > 1
    all_texts = [t for b in batches for t in b]
    assert all_texts == texts


def test_batch_by_tokens_empty():
    assert batch_by_tokens([]) == []
