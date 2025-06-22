import pytest
from sqlalchemy.orm import Session

from app.db import database


def test_engine_creation():
    # The engine should be created and bound to the correct URL
    assert database.engine is not None
    assert hasattr(database.engine, "connect")


def test_sessionlocal_returns_session():
    # SessionLocal() should return a Session instance
    session = database.SessionLocal()
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_base_is_declarative_base():
    # Base should be a declarative base class
    assert hasattr(database.Base, "metadata")


def test_get_db_yields_session():
    # get_db should yield a session and close it after use
    gen = database.get_db()
    session = next(gen)
    assert isinstance(session, Session)
    # After closing, generator should raise StopIteration
    with pytest.raises(StopIteration):
        next(gen)
