"""sanitize_arguer_replies strips task-completion leaks."""

from utils.arguer_sanitize import sanitize_arguer_replies


def test_task_completed_replaced():
    out = sanitize_arguer_replies(["Task completed."], "human: hi", "general")
    assert len(out) == 1
    assert "task completed" not in out[0].lower()
    assert len(out[0]) > 5


def test_normal_reply_unchanged():
    out = sanitize_arguer_replies(["Still not giving the money back."], "human: hi", "general")
    assert out == ["Still not giving the money back."]
