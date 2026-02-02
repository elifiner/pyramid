import pytest
import json
import tempfile
import os
from loaders import get_week_key, group_messages_by_week, load_claude_messages, load_openclaw_messages


def test_get_week_key_basic():
    assert get_week_key('2025-01-15T10:30:00') == '2025-W03'


def test_get_week_key_with_z():
    assert get_week_key('2025-01-15T10:30:00Z') == '2025-W03'


def test_get_week_key_with_timezone():
    assert get_week_key('2025-01-15T10:30:00+00:00') == '2025-W03'


def test_get_week_key_empty():
    assert get_week_key('') == 'unknown'


def test_get_week_key_none():
    assert get_week_key(None) == 'unknown'


def test_group_messages_by_week_single_week():
    messages = [
        {'content': 'Hello', 'timestamp': '2025-01-15T10:00:00'},
        {'content': 'World', 'timestamp': '2025-01-16T10:00:00'},
    ]
    by_week = group_messages_by_week(messages)
    assert '2025-W03' in by_week
    assert len(by_week['2025-W03']) == 2


def test_group_messages_by_week_multiple_weeks():
    messages = [
        {'content': 'Week 1', 'timestamp': '2025-01-06T10:00:00'},
        {'content': 'Week 2', 'timestamp': '2025-01-13T10:00:00'},
        {'content': 'Week 3', 'timestamp': '2025-01-20T10:00:00'},
    ]
    by_week = group_messages_by_week(messages)
    assert len(by_week) == 3


def test_group_messages_by_week_missing_timestamp():
    messages = [
        {'content': 'Has timestamp', 'timestamp': '2025-01-15T10:00:00'},
        {'content': 'No timestamp'},
    ]
    by_week = group_messages_by_week(messages)
    assert 'unknown' in by_week
    assert len(by_week['unknown']) == 1


def test_load_claude_messages():
    data = [{
        'uuid': 'test-conv',
        'chat_messages': [
            {
                'sender': 'human',
                'content': [{'type': 'text', 'text': 'Hello'}],
                'created_at': '2025-01-15T10:00:00Z'
            },
            {
                'sender': 'assistant',
                'content': [{'type': 'text', 'text': 'Hi there'}],
                'created_at': '2025-01-15T10:01:00Z'
            }
        ]
    }]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        
        messages, info = load_claude_messages(f.name)
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Hello'
        assert messages[1]['role'] == 'assistant'
        assert info is None


def test_load_claude_messages_with_limit():
    data = [{
        'uuid': 'test-conv',
        'chat_messages': [
            {'sender': 'human', 'content': [{'type': 'text', 'text': f'Msg {i}'}], 'created_at': f'2025-01-15T10:0{i}:00Z'}
            for i in range(5)
        ]
    }]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        
        messages, _ = load_claude_messages(f.name, limit=2)
        assert len(messages) == 2


def test_load_claude_messages_multipart_content():
    data = [{
        'uuid': 'test-conv',
        'chat_messages': [{
            'sender': 'human',
            'content': [
                {'type': 'text', 'text': 'Part 1'},
                {'type': 'text', 'text': 'Part 2'}
            ],
            'created_at': '2025-01-15T10:00:00Z'
        }]
    }]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        
        messages, _ = load_claude_messages(f.name)
        assert messages[0]['content'] == 'Part 1\nPart 2'


def test_load_openclaw_messages():
    records = [
        {'type': 'session', 'id': 'test-session', 'timestamp': '2025-01-15T10:00:00Z'},
        {
            'type': 'message',
            'timestamp': '2025-01-15T10:00:00Z',
            'message': {
                'role': 'user',
                'content': [{'type': 'text', 'text': 'Hello'}],
                'timestamp': 1736935200000
            }
        },
        {
            'type': 'message',
            'timestamp': '2025-01-15T10:01:00Z',
            'message': {
                'role': 'assistant',
                'content': [
                    {'type': 'thinking', 'thinking': 'Should not be included'},
                    {'type': 'text', 'text': 'Hi there'}
                ],
                'timestamp': 1736935260000
            }
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
        f.flush()
        
        messages, info = load_openclaw_messages(f.name)
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == 'Hello'
        assert messages[1]['role'] == 'assistant'
        assert messages[1]['content'] == 'Hi there'
        assert info is None


def test_load_openclaw_messages_skips_tool_results():
    records = [
        {
            'type': 'message',
            'message': {
                'role': 'user',
                'content': [{'type': 'text', 'text': 'Hello'}],
                'timestamp': 1736935200000
            }
        },
        {
            'type': 'message',
            'message': {
                'role': 'toolResult',
                'content': [{'type': 'text', 'text': 'Tool output'}],
                'timestamp': 1736935230000
            }
        },
        {
            'type': 'message',
            'message': {
                'role': 'assistant',
                'content': [{'type': 'text', 'text': 'Response'}],
                'timestamp': 1736935260000
            }
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
        f.flush()
        
        messages, _ = load_openclaw_messages(f.name)
        
        assert len(messages) == 2
        assert all(m['role'] in ('user', 'assistant') for m in messages)


def test_load_openclaw_messages_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        records1 = [
            {'type': 'message', 'message': {'role': 'user', 'content': [{'type': 'text', 'text': 'First'}], 'timestamp': 1736935200000}}
        ]
        records2 = [
            {'type': 'message', 'message': {'role': 'user', 'content': [{'type': 'text', 'text': 'Second'}], 'timestamp': 1736935260000}}
        ]
        
        with open(os.path.join(tmpdir, 'session1.jsonl'), 'w') as f:
            for r in records1:
                f.write(json.dumps(r) + '\n')
        with open(os.path.join(tmpdir, 'session2.jsonl'), 'w') as f:
            for r in records2:
                f.write(json.dumps(r) + '\n')
        
        messages, _ = load_openclaw_messages(tmpdir)
        
        assert len(messages) == 2


def test_load_openclaw_messages_with_limit():
    records = [
        {'type': 'message', 'message': {'role': 'user', 'content': [{'type': 'text', 'text': f'Msg {i}'}], 'timestamp': 1736935200000 + i * 60000}}
        for i in range(5)
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
        f.flush()
        
        messages, _ = load_openclaw_messages(f.name, limit=2)
        assert len(messages) == 2
