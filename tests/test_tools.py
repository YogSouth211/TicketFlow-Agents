"""Checks for the product-guide and support-ticket tools."""

from src.tools.product_knowledge import search_product_guide
from src.tools.ticketing import create_support_ticket, get_ticket_status


def test_product_guide_returns_matching_instructions():
    result = search_product_guide.invoke({"query": "How do I invite a teammate?"})
    assert "邀请工作区成员" in result
    assert "工作邮箱" in result


def test_product_guide_accepts_chinese_question():
    result = search_product_guide.invoke({"query": "如何邀请同事加入工作区？"})
    assert "邀请工作区成员" in result
    assert "发送邀请" in result


def test_product_guide_reports_no_match():
    result = search_product_guide.invoke({"query": "configure custom workflow webhooks"})
    assert "没有匹配内容" in result


def test_ticket_status_returns_seeded_ticket():
    result = get_ticket_status.invoke({"ticket_id": "SP-1001"})
    assert "status: in_progress" in result
    assert "timezone column" in result


def test_ticket_status_validates_ticket_id():
    result = get_ticket_status.invoke({"ticket_id": "bad-id"})
    assert "should look like" in result


def test_ticket_creation_rejects_unknown_account():
    result = create_support_ticket.invoke(
        {"account_id": "unknown-999", "issue": "Export report fails", "priority": "high"}
    )
    assert "Account not found" in result
