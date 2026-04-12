"""Mediator ConnectOnion agent."""

from pathlib import Path

from connectonion import Agent

from agents._hooks import log_hook
from rag import search_documents
from tools import check_conversation_health, detect_legal_topics

_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"

mediator_agent = Agent(
    name="mediator",
    system_prompt=str(_PROMPTS / "agents" / "mediator.md"),
    tools=[
        check_conversation_health,
        detect_legal_topics,
        search_documents,
    ],
    model="co/gemini-2.5-pro",
    max_iterations=5,
    on_events=[log_hook],
)
