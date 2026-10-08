"""Chinese operator workbench for the TicketFlow Agents demo."""

import html
import logging
import re
import time
import uuid

import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agents.graph import build_graph
from src.agents.intent import asks_to_create_ticket, is_cancellation, is_confirmation
from src.config import settings
from src.db.database import verify_database
from src.db.support_data import (
    archive_article,
    dashboard_stats,
    get_ticket,
    list_accounts,
    list_articles,
    list_tickets,
    save_article,
    ticket_events,
    update_ticket,
)
from src.tools.ticketing import create_support_ticket, ticket_creation_allowed

logger = logging.getLogger(__name__)
_graph = None
_agents = {}

TICKET_HEADERS = ["工单号", "账号", "问题", "优先级", "状态", "创建时间"]
ARTICLE_HEADERS = ["ID", "标题", "关键词", "状态", "更新时间"]
EVENT_HEADERS = ["类型", "记录", "时间"]
STATUS_LABELS = {"open": "待处理", "in_progress": "处理中", "resolved": "已解决"}
PRIORITY_LABELS = {"low": "低", "normal": "普通", "high": "高"}
AGENT_NAMES = {
    "product_knowledge_agent": "产品知识智能体",
    "triage_agent": "问题排查智能体",
    "ticket_ops_agent": "工单处理智能体",
}
TOOL_NAMES = {
    "search_product_guide": "搜索产品知识",
    "get_account_context": "读取账号上下文",
    "find_related_tickets": "查找相似工单",
    "create_support_ticket": "创建工单",
    "get_ticket_status": "查询工单状态",
}


def initialize() -> None:
    global _graph, _agents
    health = verify_database()
    if health.get("status") != "healthy":
        raise RuntimeError(f"Local support database is unavailable: {health}")
    if not settings.openai_api_key:
        logger.warning("No model API key configured; UI will start in preview mode.")
        return
    _graph, _, _agents = build_graph(
        model_name=settings.model_name,
        temperature=settings.temperature,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_api_base,
    )
    logger.info("TicketFlow multi-agent graph initialized.")


def _status_html(status: str, message: str, agents: list[str] | None = None) -> str:
    palette = {"success": ("#10b981", "✓"), "error": ("#ef4444", "✗"),
               "waiting": ("#6366f1", "⏳"), "idle": ("#6b7280", "●")}
    color, icon = palette.get(status, palette["idle"])
    names = [AGENT_NAMES.get(agent, agent) for agent in dict.fromkeys(agents or [])]
    detail = f"　·　参与：{'、'.join(names)}" if names else ""
    return (f'<div class="status-pill" style="--status-color:{color};">'
            f'<span class="status-icon">{icon}</span><span>{html.escape(message + detail)}</span></div>')


def _stats_html() -> str:
    stats = dashboard_stats()
    cards = [("全部工单", stats["total"]), ("待处理", stats["open"]),
             ("处理中", stats["in_progress"]), ("已解决", stats["resolved"]),
             ("知识条目", stats["articles"])]
    return '<div class="metric-grid">' + ''.join(
        f'<div class="metric-card"><strong>{value}</strong><span>{label}</span></div>'
        for label, value in cards
    ) + '</div>'


def _ticket_rows(status: str = "全部", account_id: str = "") -> list[list]:
    return [[item["ticket_id"], item["account_id"], item["issue"],
             PRIORITY_LABELS.get(item["priority"], item["priority"]),
             STATUS_LABELS.get(item["status"], item["status"]), item["created_at"]]
            for item in list_tickets(status, account_id)]


def _article_rows() -> list[list]:
    return [[item["id"], item["title"], item["keywords"], "启用" if item["active"] else "停用", item["updated_at"]]
            for item in list_articles()]


def refresh_tickets(status: str, account_id: str):
    rows = _ticket_rows(status, account_id)
    choices = [row[0] for row in rows]
    return _stats_html(), rows, gr.update(choices=choices, value=choices[0] if choices else None)


def show_ticket(ticket_id: str):
    if not ticket_id:
        return "请选择一条工单。", []
    ticket = get_ticket(ticket_id)
    if not ticket:
        return "未找到该工单。", []
    detail = (f"### {ticket['ticket_id']} · {STATUS_LABELS.get(ticket['status'], ticket['status'])}\n"
              f"**账号**：{ticket['account_id']}　　**优先级**：{PRIORITY_LABELS.get(ticket['priority'], ticket['priority'])}\n\n"
              f"**问题描述**：{ticket['issue']}")
    events = [[{"created": "创建", "status_change": "状态更新"}.get(item["event_type"], item["event_type"]),
               item["detail"], item["created_at"]]
              for item in ticket_events(ticket_id)]
    return detail, events


def apply_ticket_update(ticket_id: str, status: str, note: str):
    message = update_ticket(ticket_id or "", status, note)
    return message, ""


def create_ticket_manually(account_id: str, issue: str, priority: str, confirmed: bool):
    if not confirmed:
        return "请先核对信息并勾选确认，再创建工单。", False
    result = create_support_ticket.invoke({"account_id": account_id, "issue": issue,
                                           "priority": priority})
    if result.startswith("Ticket "):
        return f"工单已创建：**{result.split()[1]}**。请点击下方“刷新工单”查看。", False
    messages = {
        "Invalid priority": "优先级无效。",
        "Please provide": "请把问题描述写得更具体一些。",
        "Account not found": "账号不存在，请检查账号 ID。",
    }
    return next((message for prefix, message in messages.items() if result.startswith(prefix)), result), False


def refresh_articles():
    return _stats_html(), _article_rows()


def save_knowledge(title: str, content: str, keywords: str):
    message = save_article(title, content, keywords)
    return message, _article_rows(), _stats_html()


def archive_knowledge(article_id: float | None):
    if article_id is None:
        return "请填写要停用的知识 ID。", _article_rows(), _stats_html()
    message = archive_article(int(article_id))
    return message, _article_rows(), _stats_html()


def reset_conversation():
    return [], str(uuid.uuid4()), _status_html("idle", "已开启新对话"), "尚无执行记录。", ""


def show_user_message(message, history, thread_id):
    if not message or not message.strip():
        return history, "", thread_id, _status_html("idle", "请输入问题")
    thread_id = thread_id or str(uuid.uuid4())
    return history + [{"role": "user", "content": message}], "", thread_id, _status_html("waiting", "正在分配处理…")


def generate_response(history, thread_id, pending_request=""):
    if not history:
        return history, thread_id, _status_html("idle", "请输入问题"), "尚无执行记录。", pending_request
    if not _graph:
        if settings.openai_api_key:
            initialize()
        if not _graph:
            answer = "尚未配置模型服务。请在项目根目录的 .env 文件中填写 API Key 后重启应用。"
            return history + [{"role": "assistant", "content": answer}], thread_id, _status_html("error", "尚未配置模型服务"), "模型未配置。", pending_request

    user_message = next((item["content"] for item in reversed(history) if item.get("role") == "user"), None)
    if not user_message:
        return history, thread_id, _status_html("idle", "请输入问题"), "尚无执行记录。", pending_request

    confirmed_create = False
    if pending_request:
        if is_cancellation(user_message):
            answer = "已取消创建工单，没有写入新工单。"
            return history + [{"role": "assistant", "content": answer}], thread_id, _status_html("idle", "已取消创建"), "未调用智能体或工具。", ""
        if is_confirmation(user_message):
            user_message = pending_request
            pending_request = ""
            confirmed_create = True
        else:
            pending_request = ""
    if asks_to_create_ticket(user_message) and not confirmed_create:
        answer = "收到创建工单请求。请核对账号和问题描述；回复 **确认创建** 后才会交给智能体处理，或回复 **取消**。"
        return history + [{"role": "assistant", "content": answer}], thread_id, _status_html("waiting", "等待创建确认"), "尚未调用建单工具。", user_message

    if confirmed_create:
        account_match = re.search(r"\b[a-z][a-z0-9]*-\d{3,}\b", user_message.lower())
        if not account_match:
            answer = "还缺少账号 ID，例如 acme-001；本轮没有创建工单。"
            return history + [{"role": "assistant", "content": answer}], thread_id, _status_html("error", "缺少账号 ID"), "未调用建单工具。", pending_request
        known_accounts = {item["account_id"] for item in list_accounts()}
        if account_match.group() not in known_accounts:
            answer = f"账号 {account_match.group()} 不存在，请核对后重试；本轮没有创建工单。"
            return history + [{"role": "assistant", "content": answer}], thread_id, _status_html("error", "账号不存在"), "未调用建单工具。", pending_request

    started_at = time.time()
    config = {"configurable": {"thread_id": thread_id}}
    agents_used = []
    steps = []
    seen_tool_ids = set()
    final_response = None
    triage_summary = ""
    create_attempted = False
    created_ticket_id = None
    create_error = ""

    def record_tool(item: ToolMessage, agent_name: str) -> None:
        nonlocal create_attempted, created_ticket_id, create_error
        if item.name not in TOOL_NAMES:
            return
        tool_id = item.id or (item.name, item.tool_call_id, str(item.content))
        if tool_id in seen_tool_ids:
            return
        seen_tool_ids.add(tool_id)
        steps.append(f"**{len(steps) + 1}. {AGENT_NAMES[agent_name]}** 调用{TOOL_NAMES[item.name]}")
        if item.name == "create_support_ticket":
            create_attempted = True
            match = re.search(r"Ticket (SP-[A-Z0-9]+) created", str(item.content))
            if match:
                created_ticket_id = match.group(1)
            else:
                create_error = str(item.content)

    authorization_token = ticket_creation_allowed.set(confirmed_create)
    try:
        events = _graph.stream({"messages": [HumanMessage(content=user_message)]},
                               config=config, stream_mode="updates")
        for event in events:
            for node_name, node_output in event.items():
                if node_name in AGENT_NAMES:
                    agents_used.append(node_name)
                    steps.append(f"**{len(steps) + 1}. {AGENT_NAMES[node_name]}** 接手任务")
                if isinstance(node_output, dict):
                    for item in node_output.get("messages", []):
                        if isinstance(item, ToolMessage) and node_name in AGENT_NAMES:
                            record_tool(item, node_name)
                        elif (node_name == "triage_agent" and isinstance(item, AIMessage)
                              and item.content and not item.tool_calls and item.name == "triage_agent"
                              and "Transferring back" not in str(item.content)):
                            triage_summary = str(item.content)
                        elif (node_name == "supervisor" and isinstance(item, AIMessage)
                              and item.content and not item.tool_calls and item.name == "supervisor"):
                            final_response = item.content

        if confirmed_create and not create_attempted and _agents.get("ticket_ops_agent"):
            # Supervisor may stop after triage. Finish an explicitly confirmed request once.
            agents_used.append("ticket_ops_agent")
            steps.append(f"**{len(steps) + 1}. 工单处理智能体** 补全建单流程")
            context = f"用户已经在页面确认创建工单。原始请求：{user_message}"
            if triage_summary:
                context += f"\n排查智能体的结果：{triage_summary}"
            output = _agents["ticket_ops_agent"].invoke({"messages": [HumanMessage(content=context)]})
            for item in output.get("messages", []):
                if isinstance(item, ToolMessage):
                    record_tool(item, "ticket_ops_agent")
                elif isinstance(item, AIMessage) and item.content and not item.tool_calls:
                    final_response = item.content

        if confirmed_create:
            if created_ticket_id:
                final_response = f"已创建工单 **{created_ticket_id}**，当前状态为待处理。"
                if triage_summary:
                    final_response += f"\n\n排查摘要：{triage_summary}"
            elif create_attempted:
                errors = {
                    "Account not found": "账号不存在，请核对账号 ID。",
                    "Please provide": "问题描述不够具体，请补充故障现象后重试。",
                    "Invalid priority": "优先级无效，请选择低、普通或高。",
                }
                final_response = next((message for prefix, message in errors.items()
                                       if create_error.startswith(prefix)), "工单没有创建成功，请核对信息后重试。")
            else:
                final_response = "本轮没有创建工单。请补充账号 ID 和具体问题描述后重试。"
        elif create_attempted:
            final_response = "本轮没有创建工单。若需要建单，请明确提出请求并在页面确认。"
        if final_response:
            elapsed = time.time() - started_at
            trace = "\n\n".join(steps) or "Supervisor 直接完成回复。"
            return (history + [{"role": "assistant", "content": final_response}], thread_id,
                    _status_html("success" if (not confirmed_create and not create_attempted) or created_ticket_id else "error",
                                 f"处理完成 · {elapsed:.1f} 秒", agents_used), trace, pending_request)
        return history, thread_id, _status_html("error", "暂时没有生成回复", agents_used), "\n\n".join(steps), pending_request
    except Exception:
        logger.exception("TicketFlow request failed")
        answer = (f"工单 {created_ticket_id} 已创建，但后续处理出错；请到工单工作台查看。"
                  if created_ticket_id else
                  "处理时遇到问题，无法确认是否已创建工单。请先在工单工作台核对，避免重复创建。")
        return (history + [{"role": "assistant", "content": answer}], thread_id,
                _status_html("error", "处理失败，请检查服务状态"), "\n\n".join(steps) or "处理流程中断。", pending_request)
    finally:
        ticket_creation_allowed.reset(authorization_token)


def create_app() -> gr.Blocks:
    initialize()
    with gr.Blocks(title=settings.app_title, fill_width=True) as app:
        thread_id = gr.State(value="")
        pending_request = gr.State(value="")
        gr.HTML(
            '<header class="hero"><div class="hero-topline"><span class="brand-mark">T</span>'
            '<span class="brand-name">TICKETFLOW AGENTS</span>'
            '<span class="live-badge"><i></i> 本地演示</span></div>'
            '<div class="hero-body"><div><span class="hero-eyebrow">AI CUSTOMER SUPPORT WORKSPACE</span>'
            f'<h1>{settings.app_title}</h1>'
            '<p>从客户提问到问题排查、工单处理，在一个工作台完成。</p></div>'
            '<div class="hero-flow"><span>01 智能分流</span><b>→</b>'
            '<span>02 专职处理</span><b>→</b><span>03 结果留存</span></div></div></header>'
        )
        with gr.Tabs(elem_classes=["workspace-tabs"]):
            with gr.Tab("智能协作"):
                gr.HTML('<div class="section-heading"><div><span class="section-kicker">智能协作</span>'
                        '<h2>描述你的问题</h2><p>选择示例或直接输入，观察智能体如何分工处理。</p>'
                        '</div><span class="workspace-tag">三智能体协同</span></div>')
                with gr.Row(elem_classes=["chat-workspace"]):
                    with gr.Column(scale=7):
                        with gr.Group(elem_classes=["chat-panel"]):
                            chatbot = gr.Chatbot(value=[], height=235, show_label=False,
                                                 elem_classes=["chatbot-container"],
                                                 placeholder="从这里开始：咨询产品功能、排查问题，或创建和查询工单。")
                            status = gr.HTML(value=_status_html("idle", "系统已就绪，等待你的问题"),
                                             elem_classes=["status-bar"])
                            with gr.Row(elem_classes=["composer-row"]):
                                message_input = gr.Textbox(placeholder="输入产品问题或工单需求…",
                                                           show_label=False, scale=7, container=False,
                                                           lines=1, max_lines=4)
                                send_button = gr.Button("发送消息　↑", variant="primary", scale=1, min_width=120)
                            with gr.Row(elem_classes=["action-row"]):
                                gr.HTML('<span class="examples-label">快捷提问</span>')
                                prompt_a = gr.Button("如何邀请同事？", size="sm")
                                prompt_b = gr.Button("排查导出失败", size="sm")
                                prompt_c = gr.Button("创建工单", size="sm")
                                prompt_d = gr.Button("查询 SP-1001", size="sm")
                                reset_button = gr.Button("新建对话", size="sm")
                    with gr.Column(scale=3, elem_classes=["trace-panel"]):
                        gr.HTML('<div class="trace-heading"><span class="trace-symbol">↗</span>'
                                '<div><strong>执行过程</strong><small>本轮智能体与工具调用</small></div></div>')
                        trace = gr.Markdown(value="尚无执行记录。")
                        gr.HTML('<div class="agent-legend"><span>专职分工</span>'
                                '<div>◈ 产品知识　◈ 问题排查　◈ 工单处理</div></div>')

            with gr.Tab("工单工作台"):
                gr.HTML('<div class="section-heading"><div><span class="section-kicker">工单工作台</span>'
                        '<h2>跟进每一条问题</h2><p>查看工单、记录处理进展，并把状态同步给智能体。</p></div></div>')
                ticket_stats = gr.HTML(value=_stats_html())
                with gr.Row(elem_classes=["workbench-grid"]):
                    with gr.Column(scale=7, elem_classes=["surface-panel"]):
                        gr.HTML('<div class="panel-heading"><strong>工单列表</strong>'
                                '<span>最近 200 条 · 筛选后刷新</span></div>')
                        with gr.Row(elem_classes=["filter-row"]):
                            status_filter = gr.Dropdown(
                                [("全部状态", "全部"), ("待处理", "open"),
                                 ("处理中", "in_progress"), ("已解决", "resolved")],
                                value="全部", label="状态", scale=2)
                            account_filter = gr.Textbox(label="账号", placeholder="如 acme-001", scale=3)
                            refresh_button = gr.Button("刷新列表", scale=1)
                        ticket_table = gr.Dataframe(value=_ticket_rows(), headers=TICKET_HEADERS,
                                                    interactive=False, wrap=True, label="工单")
                    with gr.Column(scale=5, elem_classes=["surface-panel"]):
                        gr.HTML('<div class="panel-heading"><strong>工单详情</strong>'
                                '<span>查看与更新处理状态</span></div>')
                        ticket_select = gr.Dropdown(choices=[row[0] for row in _ticket_rows()],
                                                    label="选择工单")
                        ticket_detail = gr.Markdown("选择工单后查看详情。")
                        gr.HTML('<div class="panel-subheading">处理记录</div>')
                        event_table = gr.Dataframe(value=[], headers=EVENT_HEADERS,
                                                   interactive=False, label="历史记录")
                        new_status = gr.Dropdown(
                            [("待处理", "open"), ("处理中", "in_progress"), ("已解决", "resolved")],
                            value="in_progress", label="更新状态")
                        note = gr.Textbox(label="处理记录", lines=2,
                                          placeholder="例如：已复现并交给开发排查")
                        update_button = gr.Button("保存处理结果", variant="primary")
                        update_message = gr.Markdown()
                with gr.Accordion("＋ 人工创建工单", open=False, elem_classes=["create-accordion"]):
                    with gr.Row():
                        manual_account = gr.Dropdown(["acme-001", "northstar-002"],
                                                     value="acme-001", label="演示账号")
                        manual_priority = gr.Dropdown(
                            [("低", "low"), ("普通", "normal"), ("高", "high")],
                            value="normal", label="优先级")
                    manual_issue = gr.Textbox(label="问题描述", lines=2,
                                              placeholder="描述故障现象，至少 8 个字")
                    manual_confirm = gr.Checkbox(label="我已核对账号和问题描述，确认创建工单", value=False)
                    manual_create = gr.Button("创建工单", variant="primary")
                    manual_result = gr.Markdown()

            with gr.Tab("知识库"):
                gr.HTML('<div class="section-heading"><div><span class="section-kicker">产品知识库</span>'
                        '<h2>管理可引用的答案</h2>'
                        '<p>维护产品指南，智能体下一轮提问即可使用启用的内容。</p></div></div>')
                knowledge_stats = gr.HTML(value=_stats_html())
                with gr.Row(elem_classes=["workbench-grid"]):
                    with gr.Column(scale=7, elem_classes=["surface-panel"]):
                        gr.HTML('<div class="panel-heading"><strong>知识条目</strong>'
                                '<span>只有启用的内容会参与检索</span></div>')
                        refresh_articles_button = gr.Button("刷新知识库")
                        article_table = gr.Dataframe(value=_article_rows(), headers=ARTICLE_HEADERS,
                                                     interactive=False, wrap=True, label="全部知识")
                        gr.HTML('<div class="panel-subheading">停用一条知识</div>')
                        with gr.Row():
                            article_id = gr.Number(label="知识 ID", precision=0)
                            archive_button = gr.Button("停用知识")
                    with gr.Column(scale=5, elem_classes=["surface-panel"]):
                        gr.HTML('<div class="panel-heading"><strong>新增或更新知识</strong>'
                                '<span>同名标题会更新原内容</span></div>')
                        title = gr.Textbox(label="标题", placeholder="例如：查看账单")
                        keywords = gr.Textbox(label="关键词（逗号分隔）", placeholder="账单,付款,billing")
                        content = gr.Textbox(label="指南正文", lines=7,
                                             placeholder="写清楚用户应到哪里操作，以及需要注意的条件。")
                        save_button = gr.Button("保存知识", variant="primary")
                        article_message = gr.Markdown()

        gr.HTML('<footer class="app-footer"><span>TicketFlow Agents 多智能体客服</span>'
                '<span>演示账号 acme-001 / northstar-002 · 本地 SQLite 数据</span></footer>')

        examples = (
            (prompt_a, "如何邀请同事加入工作区？"),
            (prompt_b, "帮我排查 acme-001 的报表导出失败，看看有没有相似历史工单"),
            (prompt_c, "帮我为 acme-001 创建一个高优先级工单：点击导出报告后提示失败，无法下载 CSV 文件"),
            (prompt_d, "SP-1001 现在是什么状态？"),
        )
        for button, prompt in examples:
            button.click(fn=lambda value=prompt: value, outputs=message_input)
        for trigger in (send_button.click, message_input.submit):
            trigger(fn=show_user_message, inputs=[message_input, chatbot, thread_id],
                    outputs=[chatbot, message_input, thread_id, status]).then(
                fn=generate_response, inputs=[chatbot, thread_id, pending_request],
                outputs=[chatbot, thread_id, status, trace, pending_request])
        reset_button.click(fn=reset_conversation, outputs=[chatbot, thread_id, status, trace, pending_request])

        refresh_button.click(fn=refresh_tickets, inputs=[status_filter, account_filter],
                             outputs=[ticket_stats, ticket_table, ticket_select])
        manual_create.click(fn=create_ticket_manually,
                            inputs=[manual_account, manual_issue, manual_priority, manual_confirm],
                            outputs=[manual_result, manual_confirm]).then(
            fn=refresh_tickets, inputs=[status_filter, account_filter],
            outputs=[ticket_stats, ticket_table, ticket_select])
        ticket_select.change(fn=show_ticket, inputs=ticket_select,
                             outputs=[ticket_detail, event_table])
        update_button.click(fn=apply_ticket_update, inputs=[ticket_select, new_status, note],
                            outputs=[update_message, note]).then(
            fn=refresh_tickets, inputs=[status_filter, account_filter],
            outputs=[ticket_stats, ticket_table, ticket_select]).then(
            fn=show_ticket, inputs=ticket_select, outputs=[ticket_detail, event_table])
        refresh_articles_button.click(fn=refresh_articles, outputs=[knowledge_stats, article_table])
        save_button.click(fn=save_knowledge, inputs=[title, content, keywords],
                          outputs=[article_message, article_table, knowledge_stats])
        archive_button.click(fn=archive_knowledge, inputs=article_id,
                             outputs=[article_message, article_table, knowledge_stats])
    return app
