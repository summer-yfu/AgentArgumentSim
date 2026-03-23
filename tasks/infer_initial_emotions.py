from __future__ import annotations

import logging
from pathlib import Path

from connectonion import llm_do

from schemas import InitialEmotions, SessionState
from utils import normalize_emotion

log = logging.getLogger(__name__)
INFER_EMOTIONS_PROMPT = (
    Path(__file__).parent.parent / "prompts" / "tasks" / "infer_initial_emotions.md"
).read_text()


def infer_initial_emotions(state: SessionState) -> tuple[str, str]:
    combined = (state.background or "").strip()
    if not combined or combined.lower() == "no background provided.":
        return ("neutral", "neutral")

    prompt = (
        f"relationship: {state.relationship}\n"
        f"player_role: {state.player_role or 'N/A'}\n"
        f"ai_role: {state.ai_role or 'N/A'}\n"
        f"ai_personality: {state.ai_personality}\n"
        f"player_goal: {state.player_goal}\n"
        f"ai_goal: {state.ai_goal}\n"
        f"player_stance: {state.player_stance}\n"
        f"ai_stance: {state.ai_stance}\n"
        f"background: {state.background}\n"
    )
    try:
        out = llm_do(
            prompt,
            system_prompt=INFER_EMOTIONS_PROMPT,
            model="co/gemini-2.5-flash",
            temperature=0.2,
            output=InitialEmotions,
        )
        return (
            normalize_emotion(out.player_emotion),
            normalize_emotion(out.ai_emotion),
        )
    except Exception as e:
        log.warning("infer_initial_emotions failed: %s", e, exc_info=True)
        return ("neutral", "neutral")
