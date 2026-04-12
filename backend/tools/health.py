"""Health scores for mediator gating; phrase list for player quit."""

from __future__ import annotations

from typing import Any

from config.constants import (
    MAX_ROUNDS,
    OFF_TOPIC_THRESHOLD,
    PLAYER_STOP_MIN_LENGTH,
    PLAYER_STOP_PHRASES,
    REPETITION_STOP,
    REPETITION_STOP_MIN_ROUNDS,
    REPETITION_WARNING,
    REPETITION_WARNING_COOLDOWN,
    REPETITION_WARNING_MIN_ROUNDS,
    TOXICITY_STOP,
    TOXICITY_WARNING,
)


def check_conversation_health(
    toxicity: float,
    repetition_score: float,
    off_topic_score: float,
    rounds: int,
    goal_reached: bool,
    rounds_since_last_repetition_warning: int = 999,
) -> dict[str, Any]:
    toxicity_zone = "safe"
    if toxicity >= TOXICITY_STOP:
        toxicity_zone = "critical"
    elif toxicity >= TOXICITY_WARNING:
        toxicity_zone = "warning"

    repetition_zone = "safe"
    if repetition_score >= REPETITION_STOP and rounds >= REPETITION_STOP_MIN_ROUNDS:
        repetition_zone = "critical"
    elif repetition_score >= REPETITION_WARNING and rounds >= REPETITION_WARNING_MIN_ROUNDS:
        if rounds_since_last_repetition_warning >= REPETITION_WARNING_COOLDOWN:
            repetition_zone = "warning"

    off_topic = off_topic_score >= OFF_TOPIC_THRESHOLD
    game_ending = goal_reached or rounds >= MAX_ROUNDS

    recommended_action = "no_action"
    reason_parts: list[str] = []

    if toxicity_zone == "critical":
        recommended_action = "toxicity_stop"
        reason_parts.append(f"toxicity={toxicity:.2f} is critical (>= {TOXICITY_STOP})")
    elif game_ending:
        recommended_action = "game_end"
        reason_parts.append("goal_reached" if goal_reached else f"rounds={rounds} >= {MAX_ROUNDS}")
    elif repetition_zone == "critical":
        recommended_action = "repetition_stop"
        reason_parts.append(f"repetition={repetition_score:.2f} is critical and rounds={rounds}")
    elif toxicity_zone == "warning":
        recommended_action = "toxicity_warning"
        reason_parts.append(f"toxicity={toxicity:.2f} is in warning zone (>= {TOXICITY_WARNING})")
    elif repetition_zone == "warning":
        recommended_action = "repetition_warning"
        reason_parts.append(f"repetition={repetition_score:.2f} is stalling")
    elif off_topic:
        recommended_action = "off_topic"
        reason_parts.append(f"off_topic_score={off_topic_score:.2f} is high")

    return {
        "toxicity_zone": toxicity_zone,
        "repetition_zone": repetition_zone,
        "off_topic": off_topic,
        "game_ending": game_ending,
        "recommended_action": recommended_action,
        "reason": "; ".join(reason_parts) if reason_parts else "conversation is healthy; no intervention",
    }


def player_wants_to_stop(text: str) -> bool:
    t = (text or "").strip().lower()
    if len(t) < PLAYER_STOP_MIN_LENGTH:
        return False
    return any(phrase in t for phrase in PLAYER_STOP_PHRASES)
