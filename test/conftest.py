import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, Model, Observation, Summary


@pytest.fixture
def session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    for name in ['assistant', 'user']:
        sess.add(Model(name=name, is_base=True))
    sess.commit()
    yield sess
    sess.close()


@pytest.fixture
def user_model(session):
    return session.query(Model).filter_by(name='user').first()


@pytest.fixture
def assistant_model(session):
    return session.query(Model).filter_by(name='assistant').first()
