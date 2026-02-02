import pytest
from generate import render_memory_index, CORE_MODEL_FILES, TIER_LABELS


def test_render_memory_index_core_only():
    core_models = [
        ({'description': 'The AI assistant'}, 'SOUL.md'),
        ({'description': 'Primary user'}, 'USER.md'),
    ]
    
    content = render_memory_index(core_models, [])
    
    assert '# Memory' in content
    assert '## Core' in content
    assert '[SOUL.md](SOUL.md)' in content
    assert '[USER.md](USER.md)' in content
    assert '## Models' not in content


def test_render_memory_index_with_other_models():
    core_models = [
        ({'description': 'The AI assistant'}, 'SOUL.md'),
    ]
    other_models = [
        ({'description': 'Python project'}, 'models/python.md'),
        ({'description': 'Japan trip'}, 'models/japan-2025.md'),
    ]
    
    content = render_memory_index(core_models, other_models)
    
    assert '## Core' in content
    assert '## Models' in content
    assert 'models/python.md' in content
    assert 'models/japan-2025.md' in content


def test_render_memory_index_empty_description():
    core_models = [
        ({'description': None}, 'SOUL.md'),
    ]
    
    content = render_memory_index(core_models, [])
    assert '[SOUL.md](SOUL.md):' in content


def test_core_model_files():
    assert CORE_MODEL_FILES['assistant'] == 'SOUL.md'
    assert CORE_MODEL_FILES['user'] == 'USER.md'


def test_tier_labels():
    assert TIER_LABELS[0] == 'Recent'
    assert TIER_LABELS[1] == 'This Month'
    assert TIER_LABELS[2] == 'Historical'
