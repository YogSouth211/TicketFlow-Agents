"""Small, explicit SQLite operations shared by the agents and the operator UI."""

import re
from sqlalchemy import text

from src.db.database import get_engine


def list_accounts() -> list[dict]:
    with get_engine().connect() as conn:
        rows = conn.execute(text("SELECT account_id, company_name, plan FROM accounts ORDER BY company_name"))
        return [dict(row) for row in rows.mappings()]


def list_tickets(status: str = "全部", account_id: str = "") -> list[dict]:
    sql = """SELECT ticket_id, account_id, issue, priority, status, created_at
             FROM support_tickets WHERE (:status = '全部' OR status = :status)
             AND (:account_id = '' OR account_id = :account_id)
             ORDER BY created_at DESC, ticket_id DESC LIMIT 200"""
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), {"status": status, "account_id": account_id.strip().lower()})
        return [dict(row) for row in rows.mappings()]


def get_ticket(ticket_id: str) -> dict | None:
    with get_engine().connect() as conn:
        row = conn.execute(text("""SELECT ticket_id, account_id, issue, priority, status, created_at
                                   FROM support_tickets WHERE ticket_id = :ticket_id"""),
                           {"ticket_id": ticket_id.strip().upper()}).mappings().one_or_none()
        return dict(row) if row else None


def ticket_events(ticket_id: str) -> list[dict]:
    with get_engine().connect() as conn:
        rows = conn.execute(text("""SELECT event_type, detail, created_at FROM ticket_events
                                    WHERE ticket_id = :ticket_id ORDER BY id DESC LIMIT 30"""),
                            {"ticket_id": ticket_id.strip().upper()})
        return [dict(row) for row in rows.mappings()]


def update_ticket(ticket_id: str, status: str, note: str) -> str:
    ticket_id = ticket_id.strip().upper()
    if status not in {"open", "in_progress", "resolved"}:
        return "请选择有效的工单状态。"
    if not note.strip():
        return "请填写处理记录，方便之后追踪。"
    with get_engine().begin() as conn:
        old = conn.execute(text("SELECT status FROM support_tickets WHERE ticket_id = :id"), {"id": ticket_id}).scalar_one_or_none()
        if old is None:
            return "未找到该工单。"
        conn.execute(text("UPDATE support_tickets SET status = :status WHERE ticket_id = :id"),
                     {"status": status, "id": ticket_id})
        conn.execute(text("""INSERT INTO ticket_events (ticket_id, event_type, detail)
                             VALUES (:id, 'status_change', :detail)"""),
                     {"id": ticket_id, "detail": f"{old} → {status}；处理记录：{note.strip()}"})
    return f"已更新 {ticket_id}：{old} → {status}。"


def list_articles(active_only: bool = False) -> list[dict]:
    with get_engine().connect() as conn:
        rows = conn.execute(text("""SELECT id, title, content, keywords, active, updated_at
                                    FROM knowledge_articles WHERE (:active_only = 0 OR active = 1)
                                    ORDER BY id DESC"""), {"active_only": int(active_only)})
        return [dict(row) for row in rows.mappings()]


def save_article(title: str, content: str, keywords: str) -> str:
    title, content = title.strip(), content.strip()
    terms = [term.strip().lower() for term in re.split(r"[,，、]", keywords) if term.strip()]
    if len(title) < 2 or len(content) < 10 or not terms:
        return "请填写标题、至少 10 个字的正文和关键词（用逗号分隔）。"
    with get_engine().begin() as conn:
        conn.execute(text("""INSERT INTO knowledge_articles (title, content, keywords, active)
                             VALUES (:title, :content, :keywords, 1)
                             ON CONFLICT(title) DO UPDATE SET content=excluded.content,
                             keywords=excluded.keywords, active=1, updated_at=CURRENT_TIMESTAMP"""),
                     {"title": title, "content": content, "keywords": ",".join(terms)})
    return f"已保存知识：{title}。同名标题会更新原内容。"


def archive_article(article_id: int) -> str:
    with get_engine().begin() as conn:
        result = conn.execute(text("UPDATE knowledge_articles SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                              {"id": int(article_id)})
    return "已停用该知识。" if result.rowcount else "未找到该知识。"


def dashboard_stats() -> dict:
    with get_engine().connect() as conn:
        rows = conn.execute(text("SELECT status, COUNT(*) AS count FROM support_tickets GROUP BY status")).mappings()
        counts = {row["status"]: row["count"] for row in rows}
        articles = conn.execute(text("SELECT COUNT(*) FROM knowledge_articles WHERE active = 1")).scalar_one()
    return {"total": sum(counts.values()), "open": counts.get("open", 0),
            "in_progress": counts.get("in_progress", 0), "resolved": counts.get("resolved", 0),
            "articles": articles}
