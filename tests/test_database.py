"""Checks for the local SQLite demo database."""

import json

from src.db.database import get_engine


def test_seeded_accounts_exist():
    with get_engine().connect() as conn:
        rows = conn.exec_driver_sql("SELECT account_id, company_name FROM accounts ORDER BY account_id")
        data = [dict(row._mapping) for row in rows]
    assert len(data) == 2
    assert {row["account_id"] for row in data} == {"acme-001", "northstar-002"}


def test_seeded_tickets_exist():
    with get_engine().connect() as conn:
        rows = conn.exec_driver_sql("SELECT ticket_id, status FROM support_tickets ORDER BY ticket_id")
        data = [dict(row._mapping) for row in rows]
    assert len(data) == 2
    assert data[0]["ticket_id"] == "SP-1001"
