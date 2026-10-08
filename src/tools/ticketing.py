"""Tools for creating and checking support tickets."""

import re
import uuid
from contextvars import ContextVar

from langchain_core.tools import tool
from sqlalchemy import text

from src.db.database import get_engine


ticket_creation_allowed: ContextVar[bool] = ContextVar("ticket_creation_allowed", default=False)


@tool
def create_support_ticket(account_id: str, issue: str, priority: str = "normal") -> str:
    """Create a support ticket for a known account. Priority must be low, normal, or high."""
    account_id = account_id.strip().lower()
    priority = priority.strip().lower()
    if priority not in {"low", "normal", "high"}:
        return "Invalid priority. Choose low, normal, or high."
    if len(issue.strip()) < 8:
        return "Please provide a little more detail about the issue before creating a ticket."

    ticket_id = f"SP-{uuid.uuid4().hex[:6].upper()}"
    with get_engine().begin() as conn:
        account = conn.execute(
            text("SELECT company_name FROM accounts WHERE account_id = :account_id"),
            {"account_id": account_id},
        ).scalar_one_or_none()
        if account is None:
            return "Account not found. Check the account ID and try again."
        conn.execute(
            text("""
                INSERT INTO support_tickets (ticket_id, account_id, issue, priority, status)
                VALUES (:ticket_id, :account_id, :issue, :priority, 'open')
            """),
            {
                "ticket_id": ticket_id,
                "account_id": account_id,
                "issue": issue.strip(),
                "priority": priority,
            },
        )
        conn.execute(
            text("""INSERT INTO ticket_events (ticket_id, event_type, detail)
                    VALUES (:ticket_id, 'created', :detail)"""),
            {"ticket_id": ticket_id, "detail": f"创建工单；优先级：{priority}"},
        )
    return f"Ticket {ticket_id} created for {account} (priority: {priority})."


@tool("create_support_ticket")
def agent_create_support_ticket(account_id: str, issue: str, priority: str = "normal") -> str:
    """Create a support ticket only after the customer confirmed creation in the UI."""
    if not ticket_creation_allowed.get():
        return "创建工单需要先在页面确认；本轮没有写入工单。"
    return create_support_ticket.invoke({
        "account_id": account_id, "issue": issue, "priority": priority,
    })


@tool
def get_ticket_status(ticket_id: str) -> str:
    """Look up the current status of a support ticket by its SP- ticket ID."""
    normalized_id = ticket_id.strip().upper()
    if not re.fullmatch(r"SP-[A-Z0-9]{4,8}", normalized_id):
        return "Ticket ID should look like SP-1001."

    with get_engine().connect() as conn:
        row = conn.execute(
            text("""
                SELECT ticket_id, account_id, issue, priority, status, created_at
                FROM support_tickets WHERE ticket_id = :ticket_id
            """),
            {"ticket_id": normalized_id},
        ).mappings().one_or_none()
    if row is None:
        return f"No ticket found with ID {normalized_id}."
    return (
        f"Ticket {row['ticket_id']} | account {row['account_id']} | "
        f"status: {row['status']} | priority: {row['priority']} | issue: {row['issue']}"
    )


ticket_tools = [agent_create_support_ticket, get_ticket_status]
