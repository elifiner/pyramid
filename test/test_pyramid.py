import pytest
from datetime import datetime, UTC, timedelta
from db import Observation, Summary
from pyramid import get_pyramid, get_unsummarized_observations, bucket_by_time, TIME_BUCKETS


def test_get_pyramid_empty(session, user_model):
    by_tier = get_pyramid(session, user_model.id)
    assert by_tier == {}


def test_get_pyramid_single_tier(session, user_model):
    now = datetime.now(UTC)
    session.add(Summary(model_id=user_model.id, tier=0, text='Summary 1', start_timestamp=now, end_timestamp=now))
    session.add(Summary(model_id=user_model.id, tier=0, text='Summary 2', start_timestamp=now, end_timestamp=now))
    session.commit()
    
    by_tier = get_pyramid(session, user_model.id)
    assert 0 in by_tier
    assert len(by_tier[0]) == 2


def test_get_pyramid_multiple_tiers(session, user_model):
    now = datetime.now(UTC)
    session.add(Summary(model_id=user_model.id, tier=0, text='Tier 0', start_timestamp=now, end_timestamp=now))
    session.add(Summary(model_id=user_model.id, tier=1, text='Tier 1', start_timestamp=now, end_timestamp=now))
    session.add(Summary(model_id=user_model.id, tier=2, text='Tier 2', start_timestamp=now, end_timestamp=now))
    session.commit()
    
    by_tier = get_pyramid(session, user_model.id)
    assert set(by_tier.keys()) == {0, 1, 2}


def test_get_unsummarized_observations_no_summaries(session, user_model):
    session.add(Observation(text='Obs 1', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.add(Observation(text='Obs 2', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.commit()
    
    by_tier = get_pyramid(session, user_model.id)
    unsummarized = get_unsummarized_observations(session, user_model.id, by_tier)
    assert len(unsummarized) == 2


def test_get_unsummarized_observations_some_summarized(session, user_model):
    old_time = datetime.now(UTC) - timedelta(days=1)
    new_time = datetime.now(UTC)
    
    session.add(Observation(text='Old obs', timestamp=old_time, model_id=user_model.id))
    session.add(Summary(model_id=user_model.id, tier=0, text='Summary of old', start_timestamp=old_time, end_timestamp=old_time))
    session.add(Observation(text='New obs', timestamp=new_time, model_id=user_model.id))
    session.commit()
    
    by_tier = get_pyramid(session, user_model.id)
    unsummarized = get_unsummarized_observations(session, user_model.id, by_tier)
    assert len(unsummarized) == 1
    assert unsummarized[0].text == 'New obs'


def test_bucket_by_time_recent():
    ref_date = datetime.now(UTC)
    items = [
        {'end_timestamp': ref_date - timedelta(hours=1), 'text': 'Today'},
        {'end_timestamp': ref_date - timedelta(days=5), 'text': 'This week'},
    ]
    
    buckets = bucket_by_time(items, ref_date)
    assert len(buckets['Last 3 Days']) == 1
    assert len(buckets['This Week']) == 1


def test_bucket_by_time_old():
    ref_date = datetime.now(UTC)
    items = [
        {'end_timestamp': ref_date - timedelta(days=400), 'text': 'Old item'},
    ]
    
    buckets = bucket_by_time(items, ref_date)
    assert len(buckets['Earlier']) == 1


def test_bucket_by_time_all_buckets():
    ref_date = datetime.now(UTC)
    items = [
        {'end_timestamp': ref_date - timedelta(days=1), 'text': '3 days'},
        {'end_timestamp': ref_date - timedelta(days=5), 'text': 'week'},
        {'end_timestamp': ref_date - timedelta(days=15), 'text': 'month'},
        {'end_timestamp': ref_date - timedelta(days=60), 'text': 'quarter'},
        {'end_timestamp': ref_date - timedelta(days=200), 'text': 'year'},
        {'end_timestamp': ref_date - timedelta(days=500), 'text': 'earlier'},
    ]
    
    buckets = bucket_by_time(items, ref_date)
    
    assert len(buckets['Last 3 Days']) == 1
    assert len(buckets['This Week']) == 1
    assert len(buckets['This Month']) == 1
    assert len(buckets['This Quarter']) == 1
    assert len(buckets['This Year']) == 1
    assert len(buckets['Earlier']) == 1


def test_time_buckets_structure():
    labels = [label for label, _ in TIME_BUCKETS]
    assert labels == ['Last 3 Days', 'This Week', 'This Month', 'This Quarter', 'This Year', 'Earlier']
