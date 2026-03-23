"""Arguer ConnectOnion agent."""

from connectonion import Agent

from agents._hooks import log_hook
from rag import search_documents

from tools import (
    decide_next_move,
    detect_legal_topics,
    suggest_loop_breaking_strategies,
    update_opponent_personality,
    update_stance,
    validate_response,
)

arguer_agent = Agent(
    name="ai_arguer",
    system_prompt="prompts/agents/AI_arguer.md",
    tools=[
        update_opponent_personality,
        update_stance,
        decide_next_move,
        search_documents,
        suggest_loop_breaking_strategies,
        detect_legal_topics,
        validate_response,
    ],
    model="co/gemini-2.5-pro",
    on_events=[log_hook],
    max_iterations=10,
)
