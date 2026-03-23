"""Helpers to read tool calls/results from a ConnectOnion agent session dict."""

from __future__ import annotations

import json
from typing import Any


def tool_call_name(tc: Any) -> str:
    if not isinstance(tc, dict):
        return getattr(tc, "name", "") or ""
    fn = tc.get("function")
    if isinstance(fn, dict):
        return (fn.get("name") or "").strip()
    return (tc.get("name") or "").strip()


def parse_tool_content(content: Any) -> dict[str, Any] | None:
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            out = json.loads(content)
        except json.JSONDecodeError:
            return None
        return out if isinstance(out, dict) else None
    return None


def _get_session_messages(agent: Any) -> list[dict] | None:
    try:
        sess = getattr(agent, "current_session", None)
        if not isinstance(sess, dict):
            return None
        msgs = sess.get("messages")
        return msgs if isinstance(msgs, list) else None
    except Exception:
        return None


def agent_called_tool(agent: Any, tool_name: str) -> bool:
    msgs = _get_session_messages(agent)
    if not msgs:
        return False
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        for tc in m.get("tool_calls") or []:
            if tool_call_name(tc) == tool_name:
                return True
    return False


def last_validated_draft(agent: Any) -> str | None:
    """Return the `reply` arg from the last validate_response call that got valid=True."""
    msgs = _get_session_messages(agent)
    if not msgs:
        return None

    best: str | None = None
    i = 0
    while i < len(msgs):
        m = msgs[i]
        if m.get("role") != "assistant":
            i += 1
            continue
        tcs = m.get("tool_calls") or []
        if not tcs:
            i += 1
            continue
        j = i + 1
        for tc in tcs:
            if j >= len(msgs):
                break
            tm = msgs[j]
            if tm.get("role") not in ("tool", "function"):
                break
            if tool_call_name(tc) == "validate_response":
                # extract the `reply` arg the model passed in
                fn = tc.get("function") or {}
                args_raw = fn.get("arguments", "{}")
                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
                except json.JSONDecodeError:
                    args = {}
                draft = (args.get("reply") or "").strip()
                # check if the tool returned valid=True
                parsed = parse_tool_content(tm.get("content"))
                if parsed and parsed.get("valid") and draft:
                    best = draft
            j += 1
        i += 1
    return best


def last_revised_stance_from_arguer(agent: Any) -> str | None:
    msgs = _get_session_messages(agent)
    if not msgs:
        return None

    last: str | None = None
    i = 0
    while i < len(msgs):
        m = msgs[i]
        if m.get("role") != "assistant":
            i += 1
            continue
        tcs = m.get("tool_calls") or []
        if not tcs:
            i += 1
            continue
        j = i + 1
        for tc in tcs:
            if j >= len(msgs):
                break
            tm = msgs[j]
            if tm.get("role") not in ("tool", "function"):
                break
            if tool_call_name(tc) == "update_stance":
                parsed = parse_tool_content(tm.get("content"))
                if parsed:
                    rs = parsed.get("revised_stance")
                    if rs is not None and str(rs).strip():
                        last = str(rs).strip()
            j += 1
        i += 1
    return last
