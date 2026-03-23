"""Cheap checks on arguer draft text (length, meta phrases, law mode)."""

from __future__ import annotations

from typing import Any

from connectonion import xray

from config.constants import (
    BANNED_AGENT_COMPLETION_MARKERS,
    BANNED_SERVICE_PHRASES,
    MAX_REPLY_WORDS,
    SIMILARITY_PREFIX_CHARS,
)


@xray
def validate_response(
    reply: str,
    recent_history: str,
    setup_mode: str = "general",
    used_legal_evidence: bool = False,
) -> dict[str, Any]:
    reply = (reply or "").strip()
    lowered = reply.lower()
    avoid_phrases = [p.lower() for p in BANNED_SERVICE_PHRASES]

    violations: list[str] = []
    repair_instructions: list[str] = []

    if not reply:
        violations.append("empty_reply")
        repair_instructions.append("Write a short in-character reply.")

    if len(reply.split()) > MAX_REPLY_WORDS:
        violations.append("too_long")
        repair_instructions.append("Shorten it to 1-4 short sentences.")

    # Skip "policy" as a meta trigger (normal in debate text).
    meta_markers = [
        "as an ai",
        "as a language model",
        "language model",
        "system prompt",
        "hidden reasoning",
        "according to my instructions",
        "i'm an ai",
        "i am an ai",
        "json",
    ]
    if any(m in lowered for m in meta_markers):
        violations.append("meta_or_ooc")
        repair_instructions.append("Stay strictly in character. Remove meta or OOC language.")

    if any(marker in lowered for marker in BANNED_AGENT_COMPLETION_MARKERS):
        violations.append("assistant_task_meta")
        repair_instructions.append(
            "Remove task-completion or agent-style phrases (e.g. 'task completed'). "
            "Reply only as your character would in the argument."
        )

    banned_hits = [p for p in avoid_phrases if p and p in lowered]
    if banned_hits:
        violations.append("assistant_style_phrase")
        repair_instructions.append("Remove service-style or assistant-like phrasing and sound more like a real person in conflict.")

    hist = (recent_history or "").lower()
    if reply and lowered[:SIMILARITY_PREFIX_CHARS] in hist:
        violations.append("too_similar_to_recent_history")
        repair_instructions.append("Do not repeat your own recent wording. Use a new angle, question, or boundary.")

    if setup_mode == "law":
        legal_claim_like = any(term in lowered for term in ["under nsw law", "the law says", "legally", "notice period", "bond", "entry notice"])
        if legal_claim_like and not used_legal_evidence:
            violations.append("unsupported_legal_claim")
            repair_instructions.append("Do not make a specific legal claim unless it is grounded in retrieved legal excerpts.")

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "repair_instructions": repair_instructions,
    }
