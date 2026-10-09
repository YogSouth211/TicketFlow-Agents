"""Run each check against an isolated in-memory support database."""

import pytest

from src.db import database


@pytest.fixture(autouse=True)
def ensure_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    previous_engine = database._engine
    database._engine = None
    engine = database.get_engine()
    assert database.verify_database()["status"] == "healthy"
    try:
        yield engine
    finally:
        engine.dispose()
        database._engine = previous_engine
