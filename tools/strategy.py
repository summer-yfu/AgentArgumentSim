"""Arguer tools: stance, opponent read, moves, loop break hints."""

from __future__ import annotations

import logging
import re
from typing import Any

_log = logging.getLogger(__name__)

from connectonion import xray

from config.constants import (
    AI_LOSING_MIN_ROUND,
    AI_LOSING_PROGRESS,
    BANNED_SERVICE_PHRASES,
    CONCEDE_MIN_ROUND,
    LOOP_BREAK_THRESHOLD,
    NARROW_MIN_ROUND,
    PLAYER_PROGRESS_THRESHOLD,
    SOFTEN_MIN_ROUND,
    STUBBORNNESS_CONCEDE,
    STUBBORNNESS_HIGH,
    STUBBORNNESS_LOW,
    STUBBORNNESS_VERY_HIGH,
)
from tasks.infer_opponent_personality import infer_opponent_personality
from tasks.revise_stance import revise_stance_with_llm


def _first_sentence(text: str) -> str:
    t = text.strip()
    if not t:
        return t
    m = re.match(r"^(.+?[.!?])(?:\s+|$)", t, re.DOTALL)
    if m:
        return m.group(1).strip()
    return t


def _fallback_revised_stance(basis_stance: str, action: str) -> str:
    s = (basis_stance or "").strip()
    if not s:
        return ""
    if action == "hold":
        return s
    if action == "narrow":
        core = _first_sentence(s)
        if core == s and len(s) > 220:
            return s[:217].rstrip() + "..."
        return core if core else s
    if action == "soften":
        return (
            f"{s} - I'm still not abandoning my main position, but I'm willing to "
            "engage fairly with your points where they land."
        )
    if action == "shift":
        return (
            f"{s} - I'm prepared to move somewhat if we can align on the key facts "
            "and a practical way forward."
        )
    return s


@xray
def update_opponent_personality(recent_history: str, latest_human_message: str) -> dict[str, Any]:
    return infer_opponent_personality(recent_history, latest_human_message)


@xray
def update_stance(
    ai_stance: str,
    ai_personality: str,
    stubbornness: float,
    round_: int,
    opponent_traits: list[str] | None = None,
    player_goal_progress: float = 0.0,
    ai_goal_progress: float = 0.0,
) -> dict[str, Any]:
    personality = (ai_personality or "").strip().lower()
    if isinstance(opponent_traits, str):
        opponent_traits = [t.strip().lower() for t in opponent_traits.replace(",", " ").split() if t.strip()]
    opponent_traits = [t.lower() for t in (opponent_traits or [])]

    action = "hold"
    reason_parts: list[str] = []

    player_making_progress = player_goal_progress >= PLAYER_PROGRESS_THRESHOLD
    ai_losing_ground = ai_goal_progress < AI_LOSING_PROGRESS and round_ >= AI_LOSING_MIN_ROUND

    if stubbornness >= STUBBORNNESS_HIGH:
        action = "hold"
        reason_parts.append(f"stubbornness={stubbornness:.2f}; hold firm")
    elif player_making_progress and stubbornness < STUBBORNNESS_LOW and round_ >= SOFTEN_MIN_ROUND:
        action = "soften"
        reason_parts.append(f"player_goal_progress={player_goal_progress:.2f}, low stubbornness; consider softening")
    elif player_making_progress and round_ >= NARROW_MIN_ROUND:
        action = "narrow"
        reason_parts.append("player progressing; narrow stance to defensible core")
    elif ai_losing_ground and stubbornness < STUBBORNNESS_HIGH:
        action = "narrow"
        reason_parts.append("AI goal progress low; narrow to strongest point")

    if "aggressive" in opponent_traits and personality in {"calm", "logical"}:
        if action == "soften":
            action = "hold"
            reason_parts.append("aggressive opponent; hold not soften")

    if personality == "stubborn":
        if action in {"soften", "shift"}:
            action = "hold"
            reason_parts.append("stubborn personality; hold")

    guidance: dict[str, str] = {
        "hold": "Maintain your current stance. Defend it as before.",
        "soften": "You may soften your tone or acknowledge a partial point, but don't abandon your core position.",
        "narrow": "Narrow your stance to its strongest defensible core. Drop weaker sub-points.",
        "shift": "The conversation justifies adjusting your position. Shift slightly toward a realistic middle ground.",
    }

    reason_str = "; ".join(reason_parts) if reason_parts else "default hold"
    g = guidance[action]

    try:
        revised = revise_stance_with_llm(
            basis_stance=ai_stance,
            stance_action=action,
            guidance=g,
            reason=reason_str,
            ai_personality=personality,
        )
    except Exception as exc:
        _log.warning("revise_stance_with_llm failed (%s), using fallback", exc)
        revised = _fallback_revised_stance(ai_stance, action)

    return {
        "stance_action": action,
        "basis_stance": ai_stance,
        "revised_stance": revised,
        "guidance": g,
        "reason": reason_str,
    }


@xray
def decide_next_move(round_: int, stubbornness: float, personality: str, repetition_score: float = 0.0) -> dict[str, Any]:
    personality = (personality or "").strip().lower()
    high_stubborn = stubbornness >= STUBBORNNESS_HIGH
    very_high = stubbornness >= STUBBORNNESS_VERY_HIGH
    early = round_ <= 3

    move = "defend"
    secondary_move = "question"
    tone = "direct"
    should_concede = False
    should_offer_compromise = False
    should_set_boundary = False
    reply_style = "1-3 short chat-style sentences"
    prohibited_moves = ["assistant_style_reassurance", "meta_explanation", "speaker_labels"]
    avoid_phrases = BANNED_SERVICE_PHRASES[:]

    high_repetition = repetition_score >= LOOP_BREAK_THRESHOLD

    if very_high and early:
        move = "defend"
        secondary_move = "challenge_logic"
        tone = "firm"
        prohibited_moves += ["concede", "compromise", "promise_change"]
    elif high_stubborn or personality in {"stubborn", "defensive"}:
        move = "defend"
        secondary_move = "challenge_logic"
        tone = "firm"
        prohibited_moves += ["quick_concession", "overly_warm_deescalation"]
        should_set_boundary = personality == "defensive"
    elif personality == "logical":
        move = "challenge_logic"
        secondary_move = "question"
        tone = "structured"
    elif personality == "emotional":
        move = "emotional_response"
        secondary_move = "defend"
        tone = "reactive"
        should_set_boundary = True
    elif personality == "calm":
        move = "boundary"
        secondary_move = "question"
        tone = "controlled"
        should_set_boundary = True
    elif personality == "passive-aggressive":
        move = "reframe"
        secondary_move = "boundary"
        tone = "dry"
        should_set_boundary = True
    else:
        move = "defend"
        secondary_move = "question"

    if stubbornness < STUBBORNNESS_LOW and round_ >= CONCEDE_MIN_ROUND:
        should_concede = True
        should_offer_compromise = True
    elif stubbornness < STUBBORNNESS_CONCEDE:
        should_concede = True

    if high_stubborn:
        should_concede = False
        should_offer_compromise = False
        avoid_phrases += ["if it helps", "would that work for you", "let me try", "i can change"]

    if high_repetition:
        move = "reframe"
        secondary_move = "question"

    reason = (
        f"round={round_}, stubbornness={stubbornness:.2f}, personality={personality or 'unspecified'}, "
        f"repetition_score={repetition_score:.2f}"
    )

    return {
        "main_move": move,
        "secondary_move": secondary_move,
        "tone": tone,
        "should_concede": should_concede,
        "should_offer_compromise": should_offer_compromise,
        "should_set_boundary": should_set_boundary,
        "prohibited_moves": prohibited_moves,
        "avoid_phrases": avoid_phrases,
        "reply_style": reply_style,
        "reason": reason,
    }


@xray
def suggest_loop_breaking_strategies(repetition_score: float, last_main_move: str = "") -> dict[str, Any]:
    if repetition_score < LOOP_BREAK_THRESHOLD:
        return {
            "needs_loop_break": False,
            "recommended_move": "none",
            "bridge_phrase": "",
            "note": "Low repetition.",
        }

    recommended_move = "question"
    bridge_phrase = "We're going in circles."
    if last_main_move in {"question", "challenge_logic"}:
        recommended_move = "reframe"
        bridge_phrase = "You've already said that."
    elif last_main_move in {"defend", "reframe"}:
        recommended_move = "boundary"
        bridge_phrase = "We keep coming back to the same point."

    return {
        "needs_loop_break": True,
        "recommended_move": recommended_move,
        "bridge_phrase": bridge_phrase,
        "allowed_options": [
            "reframe the issue",
            "ask a pointed unanswered question",
            "set a boundary",
            "propose one concrete next step",
        ],
        "note": "Break the loop without repeating your last point verbatim.",
    }
