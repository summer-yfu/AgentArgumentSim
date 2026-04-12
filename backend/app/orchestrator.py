"""Runs one user turn: arguer, post-turn analysis, optional mediator, stop rules."""

from __future__ import annotations

import json
import logging
from typing import Any

from agents import arguer_agent, mediator_agent
from app.session import count_rounds, get_session
from config.constants import (
    HISTORY_TURNS,
    MAX_ROUNDS,
    REPETITION_STOP,
    REPETITION_STOP_MIN_ROUNDS,
    TOXICITY_STOP,
)
from schemas import SessionState
from tasks.analyze_conversation import analyze_conversation_state
from tools import player_wants_to_stop
from tools.health import check_conversation_health
from rag.context import rag_corpora_scope
from rag.corpus_resolution import effective_corpus_ids_for_session
from rag.retriever import default_collection_name
from utils import (
    agent_called_tool,
    last_revised_stance_from_arguer,
    last_validated_draft,
    recent_history_text,
    sanitize_arguer_replies,
    stubbornness_for_personality,
)

log = logging.getLogger(__name__)

REPLY_SEPARATOR = "\n---\n"
MAX_BUBBLES = 2


def _build_arguer_input(state: SessionState, human_input: str, rounds: int) -> str:
    payload = {
        "rounds": rounds,
        "setup_mode": state.setup_mode,
        "player_name": state.player_name,
        "ai_name": state.ai_name,
        "relationship": state.relationship,
        "player_role": state.player_role,
        "ai_role": state.ai_role,
        "background": state.background,
        "ai_personality": state.ai_personality,
        "player_goal": state.player_goal,
        "ai_goal": state.ai_goal,
        "player_stance": state.player_stance,
        "ai_stance": state.ai_stance,
        "stubbornness": stubbornness_for_personality(state.ai_personality),
        "player_emotion": state.player_emotion,
        "ai_emotion": state.ai_emotion,
        "toxicity": state.toxicity,
        "player_goal_progress": state.player_goal_progress,
        "ai_goal_progress": state.ai_goal_progress,
        "repetition_score": getattr(state, "repetition_score", 0.0),
        "recent_history": recent_history_text(state, turns=HISTORY_TURNS, use_display_names=True),
        "rag_corpora": list(getattr(state, "rag_corpora", []) or []),
    }
    if state.player_role and state.ai_role:
        role_block = (
            f"In this match: You are {state.ai_name} (the {state.ai_role}), "
            f"the human {state.player_name} is the {state.player_role}. "
            "Stay strictly in character. Do not break character (OOC). Reply as your character would.\n\n"
        )
    else:
        role_block = (
            f"In this match: You are {state.ai_name}. Your relationship with {state.player_name} is {state.relationship}. "
            "Stay in character. Do not go OOC. Do not acknowledge you are an AI.\n\n"
        )
    return (
        "Conversation state JSON:\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        f"{role_block}"
        "Use the recent history carefully. Do not repeat your own recent point in nearly the same words. "
        "If the human is repeating themselves, briefly acknowledge it and move the argument forward with a new point, question, concession, or concrete next step.\n\n"
        f"{state.player_name} just said: {human_input}\n"
        "Respond with your in-character message(s)."
    )


def _split_arguer_replies(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split("---") if p.strip()]
    if not parts:
        return [raw.strip() or "..."]
    return parts[:MAX_BUBBLES]


_PASS = "PASS"


def _maybe_call_mediator(
    state: SessionState, analysis: dict[str, Any], health: dict[str, Any]
) -> str:
    rounds = count_rounds(state)

    if health["recommended_action"] == "no_action":
        return ""

    log.info("Possible mediator intervention: %s", health["reason"])
    mediator_input = (
        "Conversation health data:\n"
        f"{json.dumps(analysis, ensure_ascii=False)}\n\n"
        f"check_conversation_health.recommended_action (authoritative): {health['recommended_action']}\n"
        f"check_conversation_health.reason: {health['reason']}\n\n"
        f"setup_mode: {state.setup_mode or 'general'}\n"
        f"rounds: {rounds}\n"
        f"player_name: {state.player_name}\n"
        f"ai_name: {state.ai_name}\n"
        f"player_goal: {state.player_goal}\n"
        f"ai_goal: {state.ai_goal}\n"
        f"background: {state.background}\n"
        f"rounds_since_last_repetition_warning: {rounds - state.last_repetition_warning_round}\n"
        f"recent_history:\n{recent_history_text(state, turns=HISTORY_TURNS)}\n\n"
        "Assess the conversation using your tools and decide whether to intervene."
    )
    reply = mediator_agent.input(mediator_input).strip()

    if not reply or reply.upper() == _PASS:
        log.info("Mediator decided: no intervention (PASS)")
        return ""

    if analysis.get("repetition_score", 0) >= 0.6:
        state.last_repetition_warning_round = rounds

    return reply


def _hard_stop_if_health_demands(
    health: dict[str, Any], analysis: dict[str, Any], state: SessionState
) -> str:
    """If health already says hard stop but _check_stop_conditions missed it, end the match."""
    if state.stop_match:
        return ""
    act = health.get("recommended_action", "no_action")
    if act == "toxicity_stop":
        state.stop_match = True
        state.last_stop_reason = "toxicity"
        return "toxicity"
    if act == "repetition_stop":
        state.stop_match = True
        state.last_stop_reason = "repetition"
        return "repetition"
    if act == "game_end":
        state.stop_match = True
        if analysis.get("goal_reached"):
            state.last_stop_reason = "goal_reached"
            return "goal_reached"
        state.last_stop_reason = "max_rounds"
        return "max_rounds"
    return ""


def _mediator_stop_summary(state: SessionState) -> str:
    rounds = count_rounds(state)
    mediator_input = (
        f"The human ({state.player_name}) has asked to end the match.\n"
        "Give a brief neutral wrap-up: acknowledge the discussion, thank both sides, and close.\n"
        "1-2 sentences only. Do not blame or criticize.\n\n"
        f"setup_mode: {state.setup_mode or 'general'}\n"
        f"player_goal: {state.player_goal}\n"
        f"ai_goal: {state.ai_goal}\n"
        f"rounds: {rounds}\n"
        f"background: {state.background}\n"
        f"recent_history:\n{recent_history_text(state, turns=HISTORY_TURNS)}\n"
    )
    reply = mediator_agent.input(mediator_input).strip()
    return reply if reply else "Thank you both for the discussion. The match has ended."


def _build_response(
    state: SessionState,
    *,
    replies: list[str],
    speaker: str = "ai",
    mediator_reply: str = "",
    stop_reason: str = "",
) -> dict[str, Any]:
    return {
        "reply": replies[0],
        "replies": replies,
        "speaker": speaker,
        "toxicity": state.toxicity,
        "player_emotion": state.player_emotion,
        "ai_emotion": state.ai_emotion,
        "player_goal_progress": state.player_goal_progress,
        "ai_goal_progress": state.ai_goal_progress,
        "mediator_reply": mediator_reply,
        "stop_match": state.stop_match,
        "stop_reason": stop_reason,
    }


def _check_stop_conditions(state: SessionState, analysis: dict[str, Any]) -> str:
    goal_reached = analysis.get("goal_reached", False)
    repetition = analysis.get("repetition_score", 0.0)
    rounds = count_rounds(state)

    if state.toxicity >= TOXICITY_STOP:
        reason = "toxicity"
    elif goal_reached:
        reason = "goal_reached"
    elif rounds >= MAX_ROUNDS:
        reason = "max_rounds"
    elif repetition >= REPETITION_STOP and rounds >= REPETITION_STOP_MIN_ROUNDS:
        reason = "repetition"
    else:
        return ""

    state.stop_match = True
    state.last_stop_reason = reason
    return reason


def run_turn(session_id: str, human_input: str) -> dict[str, Any]:
    state = get_session(session_id)

    if state.stop_match:
        return _build_response(
            state,
            replies=["The match has already been stopped."],
            speaker="system",
            stop_reason=state.last_stop_reason or "max_rounds",
        )

    clean_input = (human_input or "").strip()
    state.history.append({"speaker": "human", "text": clean_input})

    if player_wants_to_stop(clean_input):
        mediator_reply = _mediator_stop_summary(state)
        state.history.append({"speaker": "mediator", "text": mediator_reply})
        state.stop_match = True
        state.last_stop_reason = "player_requested"
        return _build_response(
            state,
            replies=["Alright."],
            mediator_reply=mediator_reply,
            stop_reason="player_requested",
        )

    rounds = count_rounds(state)

    log.info("Calling arguer, round=%d", rounds)
    arguer_input = _build_arguer_input(state, clean_input, rounds)
    rag_scope = effective_corpus_ids_for_session(
        getattr(state, "rag_corpora", []) or [],
        state.setup_mode or "general",
        law_default_collection=default_collection_name(),
    )
    with rag_corpora_scope(rag_scope):
        raw_reply = arguer_agent.input(arguer_input).strip()
    if not agent_called_tool(arguer_agent, "validate_response"):
        log.info("Note: arguer did not call validate_response this round")
    revised_stance = last_revised_stance_from_arguer(arguer_agent)
    if revised_stance:
        state.ai_stance = revised_stance
        log.debug("Updated session ai_stance from update_stance tool")
    raw_replies = _split_arguer_replies(raw_reply)
    hist_for_check = recent_history_text(state, turns=HISTORY_TURNS, use_display_names=False)
    draft = last_validated_draft(arguer_agent)
    replies = sanitize_arguer_replies(
        raw_replies, hist_for_check, state.setup_mode or "general",
        session_id=session_id, validated_draft=draft,
    )
    was_leaked = (replies != raw_replies)
    if was_leaked:
        state.consecutive_arguer_leaks += 1
        log.warning(
            "Arguer leaked meta-text (%r), replaced (streak=%d)",
            raw_reply[:60], state.consecutive_arguer_leaks,
        )
    else:
        state.consecutive_arguer_leaks = 0
    log.info("Arguer produced %d bubble(s), total len=%d", len(replies), sum(len(x) for x in replies))

    if state.consecutive_arguer_leaks >= 2:
        log.warning("Arguer leaked 2+ turns in a row, forcing match stop")
        state.stop_match = True
        state.last_stop_reason = "repetition"
        for reply in replies:
            state.history.append({"speaker": "ai", "text": reply})
        return _build_response(
            state,
            replies=replies,
            mediator_reply="This conversation has run its course. Thank you both.",
            stop_reason="repetition",
        )

    for reply in replies:
        state.history.append({"speaker": "ai", "text": reply})

    analysis = analyze_conversation_state(state)
    state.player_emotion = analysis["player_emotion"]
    state.ai_emotion = analysis["ai_emotion"]
    state.toxicity = analysis["toxicity"]
    state.player_goal_progress = analysis["player_goal_progress"]
    state.ai_goal_progress = analysis["ai_goal_progress"]
    state.repetition_score = analysis.get("repetition_score", 0.0)

    rounds_after = count_rounds(state)
    health = check_conversation_health(
        toxicity=state.toxicity,
        repetition_score=analysis.get("repetition_score", 0.0),
        off_topic_score=analysis.get("off_topic_score", 0.0),
        rounds=rounds_after,
        goal_reached=analysis.get("goal_reached", False),
        rounds_since_last_repetition_warning=rounds_after - state.last_repetition_warning_round,
    )

    mediator_reply = _maybe_call_mediator(state, analysis, health)
    if mediator_reply:
        log.info("Mediator intervened")
        state.history.append({"speaker": "mediator", "text": mediator_reply})

    stop_reason = _check_stop_conditions(state, analysis)
    hard = _hard_stop_if_health_demands(health, analysis, state)
    if hard:
        stop_reason = hard
        log.info("Hard stop from health.recommended_action=%s", health.get("recommended_action"))

    return _build_response(
        state,
        replies=replies,
        mediator_reply=mediator_reply,
        stop_reason=stop_reason,
    )
