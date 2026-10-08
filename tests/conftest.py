"""Shared fixtures for local support-tool checks."""

import pytest

from src.db.database import get_engine, verify_database


@pytest.fixture(scope="session", autouse=True)
def ensure_database():
    engine = get_engine()
    assert engine is not None
    assert verify_database()["status"] == "healthy"
    return engine
