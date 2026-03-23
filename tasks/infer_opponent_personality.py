"""Opponent style tags for the arguer (llm_do)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from connectonion import llm_do

from schemas import OpponentPersonalityAnalysis

log = logging.getLogger(__name__)
_PROMPT = (Path(__file__).parent.parent / "prompts" / "tasks" / "opponent_personality.md").read_text()


def _user_prompt(recent_history: str, latest_human_message: str) -> str:
    return (
        f"recent_history:\n{recent_history or '(empty)'}\n\n"
        f"latest_human_message:\n{latest_human_message or '(none)'}"
    )


def infer_opponent_personality(recent_history: str, latest_human_message: str) -> dict[str, Any]:
    try:
        out = llm_do(
            _user_prompt(recent_history, latest_human_message),
            system_prompt=_PROMPT,
            model="co/gemini-2.5-flash",
            temperature=0.2,
            output=OpponentPersonalityAnalysis,
        )
        traits = [t.strip().lower() for t in (out.opponent_traits or []) if str(t).strip()]
        if not traits:
            traits = ["neutral"]
        return {
            "opponent_traits": traits,
            "opponent_avg_message_length": float(out.opponent_avg_message_length),
            "strategy_notes": list(out.strategy_notes or []),
        }
    except Exception as e:
        log.warning("infer_opponent_personality failed: %s", e)
        return {
            "opponent_traits": ["neutral"],
            "opponent_avg_message_length": 10.0,
            "strategy_notes": ["Fallback: assume neutral opponent style."],
        }
