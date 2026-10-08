"""Read-only account and incident context for the triage specialist."""

import re

from langchain_core.tools import tool

from src.db.support_data import list_accounts, list_tickets


@tool
def get_account_context(account_id: str) -> str:
    """Look up a demo account's company, plan, and recent support tickets."""
    account_id = account_id.strip().lower()
    account = next((item for item in list_accounts() if item["account_id"] == account_id), None)
    if not account:
        return "账号不存在。请核对账号 ID。"
    tickets = list_tickets(account_id=account_id)[:5]
    recent = "；".join(f"{item['ticket_id']} {item['status']} {item['issue']}" for item in tickets)
    return f"{account['company_name']}（{account['plan']} 套餐）；近期工单：{recent or '无'}"


@tool
def find_related_tickets(issue: str) -> str:
    """Find previous support tickets with overlapping issue terms; read-only."""
    normalized = issue.lower()
    terms = set(re.findall(r"[a-z0-9]{2,}", normalized))
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        terms.update(phrase[index:index + 2] for index in range(len(phrase) - 1))
    aliases = {
        "导出": {"export", "csv", "report"},
        "报表": {"report", "export"},
        "邀请": {"invite", "member"},
        "登录": {"login", "sign"},
        "密码": {"password", "reset"},
    }
    for word, related in aliases.items():
        if word in normalized:
            terms.update(related)
    if not terms:
        return "请提供更具体的问题描述。"
    matches = []
    for ticket in list_tickets():
        issue_text = ticket.get("issue")
        if not issue_text:
            continue
        item_text = issue_text.lower()
        score = sum(term in item_text for term in terms)
        if score:
            matches.append((score, ticket))
    matches.sort(key=lambda pair: pair[0], reverse=True)
    if not matches:
        return "没有找到相似的历史工单。"
    return "\n".join(
        f"{ticket['ticket_id']}｜{ticket['status']}｜{ticket['issue']}"
        for _, ticket in matches[:5]
    )


triage_tools = [get_account_context, find_related_tickets]
