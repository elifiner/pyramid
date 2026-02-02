import pytest
from llm import estimate_tokens, chunk_messages, MAX_TOKENS


def test_estimate_tokens():
    text = "Hello world"
    tokens = estimate_tokens(text)
    assert tokens == len(text) // 4


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_chunk_messages_single_chunk():
    messages = [
        {'role': 'user', 'content': 'Hello'},
        {'role': 'assistant', 'content': 'Hi there'}
    ]
    chunks = chunk_messages(messages)
    assert len(chunks) == 1
    assert len(chunks[0]) == 2


def test_chunk_messages_splits_large():
    long_content = "x" * (MAX_TOKENS * 4 + 100)
    messages = [
        {'role': 'user', 'content': 'Short message'},
        {'role': 'assistant', 'content': long_content},
        {'role': 'user', 'content': 'Another short one'}
    ]
    chunks = chunk_messages(messages)
    assert len(chunks) >= 2


def test_chunk_messages_empty():
    chunks = chunk_messages([])
    assert chunks == []


def test_chunk_messages_preserves_order():
    messages = [{'role': 'user', 'content': f'Message {i}'} for i in range(5)]
    chunks = chunk_messages(messages)
    all_msgs = [m for chunk in chunks for m in chunk]
    assert all_msgs == messages
