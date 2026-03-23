"""Post-process arguer chat lines before they hit history."""

from __future__ import annotations

import random

from tools.validation import validate_response

_DISENGAGE_LINES = [
    "I don't have anything else to add right now.",
    "I think we've said everything we need to say.",
    "Look, I've said my piece. That's where I'm at.",
    "I'm not going to keep going in circles.",
    "We're going nowhere with this. I'm stepping back.",
    "There's nothing left to say here.",
    "I've made my position clear.",
]

_last_used: dict[str, str] = {}


def _pick_fallback(session_key: str = "") -> str:
    prev = _last_used.get(session_key, "")
    pool = [l for l in _DISENGAGE_LINES if l != prev]
    pick = random.choice(pool)
    _last_used[session_key] = pick
    return pick


def sanitize_arguer_replies(
    replies: list[str],
    recent_history: str,
    setup_mode: str,
    session_id: str = "",
    validated_draft: str | None = None,
) -> list[str]:
    mode = setup_mode or "general"
    out: list[str] = []
    for r in replies:
        text = (r or "").strip()
        if not text:
            continue
        vr = validate_response(text, recent_history, setup_mode=mode)
        if not vr["valid"] and "assistant_task_meta" in vr["violations"]:
            if validated_draft:
                out.append(validated_draft)
                validated_draft = None
            else:
                out.append(_pick_fallback(session_id))
        else:
            out.append(text)
    return out if out else ["..."]
