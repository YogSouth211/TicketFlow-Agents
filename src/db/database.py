"""SQLite storage for sample SaaS accounts and support tickets."""

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)
_engine = None
_database_path = Path(__file__).resolve().parents[2] / "supportpilot.db"


def get_engine():
    """Create the local demo database on first use."""
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL", f"sqlite:///{_database_path.as_posix()}")
        options = {"connect_args": {"check_same_thread": False}}
        if database_url == "sqlite://":
            options["poolclass"] = StaticPool
        _engine = create_engine(database_url, **options)
        _initialize_database(_engine)
    return _engine


def _initialize_database(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                plan TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                issue TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ticket_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                keywords TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            INSERT OR IGNORE INTO accounts (account_id, company_name, plan)
            VALUES
                ('acme-001', 'Acme Analytics', 'Pro'),
                ('northstar-002', 'Northstar Studio', 'Team')
        """))
        conn.execute(text("""
            INSERT OR IGNORE INTO support_tickets
                (ticket_id, account_id, issue, priority, status)
            VALUES
                ('SP-1001', 'acme-001', 'CSV export is missing the timezone column', 'normal', 'in_progress'),
                ('SP-1002', 'northstar-002', 'Unable to invite a new workspace member', 'high', 'open')
        """))
        for title, content, keywords in _SEED_ARTICLES:
            conn.execute(text("""
                INSERT OR IGNORE INTO knowledge_articles (title, content, keywords)
                VALUES (:title, :content, :keywords)
            """), {"title": title, "content": content, "keywords": keywords})


_SEED_ARTICLES = [
    ("邀请工作区成员", "打开工作区设置，进入成员页面，输入同事的工作邮箱并点击发送邀请。待接受的邀请可以在同一页面重新发送。", "邀请,同事,成员,invite,teammate,member"),
    ("导出报表", "打开报表页面，选择已保存的报表并点击导出，可选择 CSV 或 XLSX。导出时使用工作区设置的时区。", "导出,报表,报告,export,report,csv,xlsx"),
    ("重置密码", "在登录页面点击忘记密码，填写账户邮箱。重置链接有效期为 30 分钟。", "密码,重置,登录,password,reset,sign in"),
    ("管理账单联系人", "工作区管理员可以在工作区设置的账单页面更新联系人。只有管理员可以查看发票或修改付款信息。", "账单,发票,付款,billing,invoice,payment"),
    ("设置通知", "成员可以在个人设置中管理邮件通知；整个工作区的告警规则由管理员在工作区设置中管理。", "通知,提醒,告警,notification,alert"),
]


def verify_database() -> dict:
    try:
        with get_engine().connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM accounts")).scalar_one()
        return {"status": "healthy", "accounts": count}
    except Exception as exc:
        logger.exception("Support database check failed")
        return {"status": "unhealthy", "error": str(exc)}
