"""Mediator ConnectOnion agent."""

from connectonion import Agent

from agents._hooks import log_hook
from rag import search_documents
from tools import check_conversation_health, detect_legal_topics

mediator_agent = Agent(
    name="mediator",
    system_prompt="prompts/agents/mediator.md",
    tools=[
        check_conversation_health,
        detect_legal_topics,
        search_documents,
    ],
    model="co/gemini-2.5-pro",
    max_iterations=5,
    on_events=[log_hook],
)
