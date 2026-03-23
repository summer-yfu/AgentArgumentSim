"""last_revised_stance_from_arguer parsing."""

from __future__ import annotations

import json

from utils.agent_tool_messages import last_revised_stance_from_arguer


class _FakeArguer:
    def __init__(self, messages: list) -> None:
        self.current_session = {"messages": messages}


def test_last_revised_stance_parses_tool_message():
    payload = {"revised_stance": "I still disagree on the bond.", "stance_action": "hold"}
    msgs = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "tool_calls": [{"type": "function", "function": {"name": "update_stance", "arguments": "{}"}}],
        },
        {"role": "tool", "content": json.dumps(payload)},
    ]
    assert last_revised_stance_from_arguer(_FakeArguer(msgs)) == "I still disagree on the bond."


def test_last_revised_stance_takes_final_call():
    first = {"revised_stance": "First version", "stance_action": "narrow"}
    second = {"revised_stance": "Final version", "stance_action": "soften"}
    msgs = [
        {
            "role": "assistant",
            "tool_calls": [{"function": {"name": "update_stance", "arguments": "{}"}}],
        },
        {"role": "tool", "content": json.dumps(first)},
        {
            "role": "assistant",
            "tool_calls": [{"function": {"name": "other_tool", "arguments": "{}"}}],
        },
        {"role": "tool", "content": "{}"},
        {
            "role": "assistant",
            "tool_calls": [{"function": {"name": "update_stance", "arguments": "{}"}}],
        },
        {"role": "tool", "content": json.dumps(second)},
    ]
    assert last_revised_stance_from_arguer(_FakeArguer(msgs)) == "Final version"
