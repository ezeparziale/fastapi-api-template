import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import database


def test_engine_creation() -> None:
    # The engine should be created and bound to the correct URL
    assert database.engine is not None
    assert hasattr(database.engine, "connect")


def test_engine_applies_statement_timeout() -> None:
    with database.engine.connect() as connection:
        statement_timeout = connection.execute(
            text("SHOW statement_timeout")
        ).scalar_one()

    assert statement_timeout != "0"


def test_sessionlocal_returns_session() -> None:
    # SessionLocal() should return a Session instance
    session = database.SessionLocal()
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_base_is_declarative_base() -> None:
    # Base should be a declarative base class
    assert hasattr(database.Base, "metadata")


def test_foreign_keys_are_indexed() -> None:
    posts = database.Base.metadata.tables["posts"]
    votes = database.Base.metadata.tables["votes"]

    assert "ix_posts_owner_id" in {index.name for index in posts.indexes}
    assert "ix_votes_post_id" in {index.name for index in votes.indexes}


def test_constraints_use_alembic_naming_convention() -> None:
    metadata = database.Base.metadata

    def constraint_names(table_name: str) -> set[str]:
        return {
            constraint.name
            for constraint in metadata.tables[table_name].constraints
            if isinstance(constraint.name, str)
        }

    assert "pk_users" in constraint_names("users")
    assert "uq_users_email" in constraint_names("users")
    assert "pk_posts" in constraint_names("posts")
    assert "fk_posts_owner_id_users" in constraint_names("posts")
    assert "pk_votes" in constraint_names("votes")
    assert "fk_votes_user_id_users" in constraint_names("votes")
    assert "fk_votes_post_id_posts" in constraint_names("votes")
    assert "pk_users_credit_cards" in constraint_names("users_credit_cards")
    assert "uq_users_credit_cards_user_id" in constraint_names("users_credit_cards")
    assert "fk_users_credit_cards_user_id_users" in constraint_names(
        "users_credit_cards"
    )


def test_get_db_yields_session() -> None:
    # get_db should yield a session and close it after use
    gen = database.get_db()
    session = next(gen)
    assert isinstance(session, Session)
    # After closing, generator should raise StopIteration
    with pytest.raises(StopIteration):
        next(gen)
