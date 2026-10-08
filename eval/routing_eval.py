"""Run labelled route cases against Qwen with an isolated in-memory SQLite DB."""

import json
import logging
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4

# Set before importing the database module: this script must not edit the user's DB.
# A temporary file works across LangGraph worker threads more reliably than one shared in-memory connection.
_temporary_db = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_temporary_db.name) / 'routing.db').as_posix()}"

from langchain_core.messages import HumanMessage, ToolMessage  # noqa: E402

from src.agents.graph import build_graph  # noqa: E402
from src.config import settings  # noqa: E402
from src.db.database import get_engine  # noqa: E402
from src.tools.ticketing import ticket_creation_allowed  # noqa: E402


AGENTS = {"product_knowledge_agent", "triage_agent", "ticket_ops_agent"}
BUSINESS_TOOLS = {
    "search_product_guide", "get_account_context", "find_related_tickets",
    "create_support_ticket", "get_ticket_status",
}
CASES_PATH = Path(__file__).with_name("routing_cases.json")
RESULTS_PATH = Path(__file__).with_name("routing_results.json")


def describe_events(events) -> tuple[list[str], list[str], bool]:
    agents, tools, seen = [], [], set()
    created = False
    for event in events:
        for node_name, output in event.items():
            if node_name not in AGENTS:
                continue
            agents.append(node_name)
            for message in output.get("messages", []):
                if not isinstance(message, ToolMessage) or message.name not in BUSINESS_TOOLS:
                    continue
                identifier = message.id or (message.name, message.tool_call_id, str(message.content))
                if identifier in seen:
                    continue
                seen.add(identifier)
                tools.append(message.name)
                if message.name == "create_support_ticket" and re.search(r"Ticket SP-[A-Z0-9]+ created", str(message.content)):
                    created = True
    return agents, tools, created


def main() -> None:
    if not settings.openai_api_key:
        raise SystemExit("缺少模型 API Key；请先配置 .env")
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    graph, _, _ = build_graph(
        model_name=settings.model_name,
        temperature=settings.temperature,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_api_base,
    )
    results = []
    for index, case in enumerate(cases, start=1):
        authorization_token = ticket_creation_allowed.set("create_support_ticket" in case["tools"])
        try:
            events = graph.stream(
                {"messages": [HumanMessage(content=case["question"])]},
                {"configurable": {"thread_id": uuid4().hex}},
                stream_mode="updates",
            )
            agents, tools, created = describe_events(events)
            passed = (agents == case["agents"] and all(tool in tools for tool in case["tools"])
                      and created == case.get("should_create", "create_support_ticket" in case["tools"]))
            results.append({**case, "actual_agents": agents, "actual_tools": tools,
                            "ticket_created": created, "passed": passed})
            print(f"{index}/{len(cases)} {'通过' if passed else '未通过'}：{agents} / {tools} / 建单={created}")
        except Exception as exc:
            results.append({**case, "passed": False, "error": type(exc).__name__})
            print(f"{index}/{len(cases)} 未完成：{type(exc).__name__}")
        finally:
            ticket_creation_allowed.reset(authorization_token)
    report = {"passed": sum(item["passed"] for item in results), "total": len(results), "cases": results}
    RESULTS_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"路由通过 {report['passed']}/{report['total']}；结果保存至 {RESULTS_PATH}")
    get_engine().dispose()
    _temporary_db.cleanup()


if __name__ == "__main__":
    main()
