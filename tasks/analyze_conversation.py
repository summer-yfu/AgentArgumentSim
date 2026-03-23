"""Post-turn metrics: emotions, toxicity, progress, etc. (llm_do)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from connectonion import llm_do

from schemas import ConversationAnalysis, SessionState
from utils import clamp, normalize_emotion, recent_history_text

log = logging.getLogger(__name__)
CONVERSATION_ANALYZER_PROMPT = (
    Path(__file__).parent.parent / "prompts" / "tasks" / "conversation_analyzer.md"
).read_text()


def _analysis_prompt(state: SessionState) -> str:
    return (
        f"Player goal: {state.player_goal}\n"
        f"AI goal: {state.ai_goal}\n\n"
        f"Player stance: {state.player_stance}\n"
        f"AI stance: {state.ai_stance}\n\n"
        f"Background:\n{state.background}\n\n"
        f"Conversation:\n{recent_history_text(state)}"
    )


def analyze_conversation_state(state: SessionState) -> dict[str, Any]:
    try:
        out = llm_do(
            _analysis_prompt(state),
            system_prompt=CONVERSATION_ANALYZER_PROMPT,
            model="co/gemini-2.5-flash",
            temperature=0.1,
            output=ConversationAnalysis,
        )
        return {
            "player_emotion": normalize_emotion(out.player_emotion),
            "ai_emotion": normalize_emotion(out.ai_emotion),
            "toxicity": clamp(out.toxicity),
            "repetition_score": clamp(out.repetition_score),
            "goal_reached": out.goal_reached,
            "off_topic_score": clamp(out.off_topic_score),
            "player_goal_progress": clamp(out.player_goal_progress),
            "ai_goal_progress": clamp(out.ai_goal_progress),
        }
    except Exception as e:
        log.warning("analyze_conversation_state failed: %s", e, exc_info=True)
        return {
            "player_emotion": "neutral",
            "ai_emotion": "neutral",
            "toxicity": 0.15,
            "repetition_score": 0.0,
            "goal_reached": False,
            "off_topic_score": 0.0,
            "player_goal_progress": 0.0,
            "ai_goal_progress": 0.0,
        }
