import pytest
from datetime import datetime, UTC
from db import Observation
from summarize import chunk_observations, get_observations_by_model, STEP


def test_get_observations_by_model(session, user_model):
    session.add(Observation(text='Obs 1', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.add(Observation(text='Obs 2', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.add(Observation(text='Obs 3', timestamp=datetime.now(UTC)))
    session.commit()
    
    by_model = get_observations_by_model(session)
    assert user_model.id in by_model
    assert len(by_model[user_model.id]) == 2


def test_chunk_observations_small(session):
    obs = Observation(text='Short observation', timestamp=datetime.now(UTC))
    session.add(obs)
    session.commit()
    
    chunks = chunk_observations([obs])
    assert len(chunks) == 1
    assert len(chunks[0]) == 1


def test_chunk_observations_exact_step(session, user_model):
    for i in range(STEP):
        session.add(Observation(text=f'Obs {i}', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.commit()
    
    obs = session.query(Observation).filter_by(model_id=user_model.id).all()
    chunks = chunk_observations(obs)
    assert len(chunks) == 1
    assert len(chunks[0]) == STEP


def test_chunk_observations_by_tokens(session, user_model):
    from llm import MAX_TOKENS
    long_text = 'x' * (MAX_TOKENS * 4)
    session.add(Observation(text='Short', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.add(Observation(text=long_text, timestamp=datetime.now(UTC), model_id=user_model.id))
    session.add(Observation(text='Short 2', timestamp=datetime.now(UTC), model_id=user_model.id))
    session.commit()
    
    obs = session.query(Observation).filter_by(model_id=user_model.id).all()
    chunks = chunk_observations(obs)
    assert len(chunks) >= 2


def test_step_constant():
    assert STEP == 10
