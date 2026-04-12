"""Logs each LLM iteration to .co/logs/iterations.jsonl and prints a one-line summary."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from connectonion import before_llm

_log = logging.getLogger("agents")

_ITER_FILE = Path(".co/logs/iterations.jsonl")
_ITER_FILE.parent.mkdir(parents=True, exist_ok=True)

_prev_count: dict[str, int] = {}


def _iteration_hook(agent):
    try:
        _iteration_hook_impl(agent)
    except Exception as exc:
        _log.warning("[%s] hook error: %s", getattr(agent, "name", "?"), exc)


def _tool_names_from(msgs: list[dict]) -> list[str]:
    names: list[str] = []
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        for tc in m.get("tool_calls") or []:
            fn = tc.get("function") or tc
            names.append(fn.get("name", "?"))
    return names


def _iteration_hook_impl(agent):
    name = agent.name
    msgs = agent.current_session.get("messages", [])
    total = len(msgs)

    prev = _prev_count.get(name, 0)
    if total <= prev:
        prev = 0
    _prev_count[name] = total

    new_msgs = msgs[prev:]
    turn_tools = _tool_names_from(new_msgs)
    all_tools = _tool_names_from(msgs)
    turn_iter = sum(1 for m in new_msgs if m.get("role") == "assistant") + 1
    session_iter = sum(1 for m in msgs if m.get("role") == "assistant") + 1

    record = {
        "agent": name,
        "turn_iteration": turn_iter,
        "session_iteration": session_iter,
        "message_count": total,
        "new_messages_since_last": len(new_msgs),
        "messages": msgs,
    }
    with _ITER_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    _log.info(
        "[%s] turn iter %d (session %d) - %d msgs, this turn tools: %s",
        name, turn_iter, session_iter, total,
        turn_tools or "none",
    )


log_hook = before_llm(_iteration_hook)
