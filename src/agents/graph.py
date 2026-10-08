"""Build the SupportPilot multi-agent supervisor graph."""

import logging

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from src.agents.prompts import (
    KNOWLEDGE_AGENT_PROMPT,
    SUPERVISOR_PROMPT,
    TICKET_AGENT_PROMPT,
    TRIAGE_AGENT_PROMPT,
)
from src.tools import knowledge_tools, ticket_tools, triage_tools

logger = logging.getLogger(__name__)


def build_graph(
    model_name: str = "qwen-plus",
    temperature: float = 0,
    openai_api_key: str | None = None,
    openai_api_base: str | None = None,
):
    """Create three specialist agents and a supervisor that routes between them."""
    llm_kwargs = {"model": model_name, "temperature": temperature}
    if openai_api_key:
        llm_kwargs["api_key"] = openai_api_key
    if openai_api_base:
        llm_kwargs["base_url"] = openai_api_base

    llm = ChatOpenAI(**llm_kwargs)
    knowledge_agent = create_react_agent(
        llm,
        tools=knowledge_tools,
        prompt=KNOWLEDGE_AGENT_PROMPT,
        name="product_knowledge_agent",
    )
    ticket_agent = create_react_agent(
        llm,
        tools=ticket_tools,
        prompt=TICKET_AGENT_PROMPT,
        name="ticket_ops_agent",
    )
    triage_agent = create_react_agent(
        llm,
        tools=triage_tools,
        prompt=TRIAGE_AGENT_PROMPT,
        name="triage_agent",
    )

    supervisor = create_supervisor(
        agents=[knowledge_agent, triage_agent, ticket_agent],
        model=llm,
        prompt=SUPERVISOR_PROMPT,
        output_mode="last_message",
    )
    checkpointer = MemorySaver()
    graph = supervisor.compile(name="supportpilot_multi_agent", checkpointer=checkpointer)
    logger.info("SupportPilot supervisor and specialist agents are ready.")
    return graph, checkpointer, None
