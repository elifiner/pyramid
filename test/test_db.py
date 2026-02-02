import pytest
from datetime import datetime, UTC
from db import Model, Observation, Summary


def test_base_models_created(session):
    models = session.query(Model).filter_by(is_base=True).all()
    names = {m.name for m in models}
    assert names == {'assistant', 'user'}


def test_add_observation_without_model(session):
    obs = Observation(text='Test observation', timestamp=datetime.now(UTC))
    session.add(obs)
    session.commit()
    
    assert obs.id is not None
    assert obs.model_id is None
    assert obs.model is None


def test_add_observation_with_model(session, assistant_model):
    obs = Observation(text='I learned something new', model_id=assistant_model.id, timestamp=datetime.now(UTC))
    session.add(obs)
    session.commit()
    
    assert obs.model.name == 'assistant'


def test_create_custom_model(session):
    model = Model(name='python', description='Programming language experiences', is_base=False)
    session.add(model)
    session.commit()
    
    assert model.id is not None
    assert not model.is_base


def test_model_has_observations(session, user_model):
    obs1 = Observation(text='Eli asked for help', model_id=user_model.id, timestamp=datetime.now(UTC))
    obs2 = Observation(text='Eli prefers simple code', model_id=user_model.id, timestamp=datetime.now(UTC))
    session.add_all([obs1, obs2])
    session.commit()
    
    session.refresh(user_model)
    assert len(user_model.observations) == 2


def test_add_summary(session, assistant_model):
    now = datetime.now(UTC)
    summary = Summary(
        model_id=assistant_model.id,
        tier=0,
        text='Learned about memory systems. IMPORTANT: pyramidal structure.',
        start_timestamp=now,
        end_timestamp=now
    )
    session.add(summary)
    session.commit()
    
    assert summary.id is not None
    assert summary.model.name == 'assistant'


def test_summary_tiers(session, user_model):
    now = datetime.now(UTC)
    t0 = Summary(model_id=user_model.id, tier=0, text='Tier 0', start_timestamp=now, end_timestamp=now)
    t1 = Summary(model_id=user_model.id, tier=1, text='Tier 1', start_timestamp=now, end_timestamp=now)
    session.add_all([t0, t1])
    session.commit()
    
    summaries = session.query(Summary).filter_by(model_id=user_model.id).order_by(Summary.tier).all()
    assert [s.tier for s in summaries] == [0, 1]
