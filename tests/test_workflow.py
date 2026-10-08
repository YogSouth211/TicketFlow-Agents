"""Checks for confirmation, fallback handoff, and truthful ticket feedback."""

from unittest.mock import patch

from langchain_core.messages import AIMessage, ToolMessage

from src.agents.intent import asks_to_create_ticket
from src.tools.triage import find_related_tickets
from src.tools.ticketing import agent_create_support_ticket, ticket_creation_allowed
from src.ui.app import create_ticket_manually, generate_response


class FakeGraph:
    def __init__(self):
        self.calls = 0

    def stream(self, payload, config, stream_mode):
        self.calls += 1
        yield {"triage_agent": {"messages": [
            ToolMessage(content="Acme Analytics", name="get_account_context", tool_call_id="a"),
            AIMessage(content="账号存在，已有相似历史工单。", name="triage_agent"),
        ]}}
        yield {"supervisor": {"messages": [
            AIMessage(content="接下来创建工单。", name="supervisor"),
        ]}}


class FakeTicketAgent:
    def __init__(self):
        self.calls = 0

    def invoke(self, payload):
        self.calls += 1
        return {"messages": [
            ToolMessage(content="Ticket SP-ABCD created for Acme Analytics (priority: high).",
                        name="create_support_ticket", tool_call_id="b"),
            AIMessage(content="工单已建立。", name="ticket_ops_agent"),
        ]}


def test_creation_intent_excludes_help_and_negation():
    assert asks_to_create_ticket("为 acme-001 创建高优先级工单：导出失败")
    assert not asks_to_create_ticket("如何创建工单？")
    assert not asks_to_create_ticket("先不要创建工单，只帮我排查")


def test_chat_requires_confirmation_then_fills_missing_ticket_handoff():
    graph, agent = FakeGraph(), FakeTicketAgent()
    original = "先排查 acme-001 的导出失败，再创建高优先级工单：CSV 无法下载"
    with patch("src.ui.app._graph", graph), patch("src.ui.app._agents", {"ticket_ops_agent": agent}), \
         patch("src.ui.app.list_accounts", return_value=[{"account_id": "acme-001"}]):
        pending = generate_response([{"role": "user", "content": original}], "thread-1")
        assert graph.calls == 0
        assert pending[4] == original
        history = pending[0] + [{"role": "user", "content": "确认创建"}]
        result = generate_response(history, "thread-1", pending[4])
    assert graph.calls == 1
    assert agent.calls == 1
    assert "SP-ABCD" in result[0][-1]["content"]
    assert "排查摘要" in result[0][-1]["content"]
    assert "创建工单" in result[3]
    assert result[4] == ""


def test_unknown_account_is_rejected_before_graph():
    graph = FakeGraph()
    with patch("src.ui.app._graph", graph), patch("src.ui.app.list_accounts", return_value=[]):
        result = generate_response([{"role": "user", "content": "确认创建"}], "thread-2",
                                   "为 missing-999 创建工单：报表下载失败")
    assert graph.calls == 0
    assert "账号 missing-999 不存在" in result[0][-1]["content"]


def test_manual_creation_requires_checkbox():
    result, checked = create_ticket_manually("acme-001", "报表下载失败", "high", False)
    assert "勾选确认" in result
    assert checked is False


def test_related_ticket_search_skips_incomplete_records():
    with patch("src.tools.triage.list_tickets", return_value=[
        {"ticket_id": "SP-BAD", "issue": None, "status": "open"},
        {"ticket_id": "SP-GOOD", "issue": "CSV export fails", "status": "open"},
    ]):
        result = find_related_tickets.invoke({"issue": "CSV 导出失败"})
    assert "SP-GOOD" in result
    assert "SP-BAD" not in result


def test_agent_ticket_tool_requires_server_side_confirmation():
    payload = {"account_id": "acme-001", "issue": "报表下载失败", "priority": "high"}
    denied = agent_create_support_ticket.invoke(payload)
    assert "需要先在页面确认" in denied
    with patch("src.tools.ticketing.create_support_ticket") as actual_tool:
        actual_tool.invoke.return_value = "Ticket SP-ABCD created for Acme Analytics."
        token = ticket_creation_allowed.set(True)
        try:
            allowed = agent_create_support_ticket.invoke(payload)
        finally:
            ticket_creation_allowed.reset(token)
    assert "SP-ABCD" in allowed
    actual_tool.invoke.assert_called_once_with(payload)
