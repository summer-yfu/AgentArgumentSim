"""utils.helpers."""

from __future__ import annotations

from schemas import SessionState
from utils import clamp, normalize_emotion, recent_history_text, stubbornness_for_personality


class TestClamp:
    def test_within_range(self):
        assert clamp(0.5) == 0.5

    def test_below_lower(self):
        assert clamp(-0.5) == 0.0

    def test_above_upper(self):
        assert clamp(1.5) == 1.0


class TestNormalizeEmotion:
    def test_allowed(self):
        assert normalize_emotion("angry") == "angry"

    def test_alias(self):
        assert normalize_emotion("frustrated") == "anxious"

    def test_unknown(self):
        assert normalize_emotion("ecstatic") == "neutral"

    def test_empty(self):
        assert normalize_emotion("") == "neutral"

    def test_none(self):
        assert normalize_emotion(None) == "neutral"


class TestStubbornness:
    def test_known_personality(self):
        assert stubbornness_for_personality("stubborn") == 0.9
        assert stubbornness_for_personality("calm") == 0.25

    def test_unknown_default(self):
        assert stubbornness_for_personality("random") == 0.55


class TestRecentHistoryText:
    def test_with_history(self, sample_state: SessionState):
        text = recent_history_text(sample_state, turns=2)
        assert "ai:" in text
        assert "human:" in text

    def test_display_names(self, sample_state: SessionState):
        text = recent_history_text(sample_state, turns=2, use_display_names=True)
        assert "Bob:" in text
        assert "Alice:" in text

    def test_empty_history(self):
        state = SessionState(
            session_id="x", player_name="A", ai_name="B", relationship="r",
            player_role="", ai_role="", ai_personality="calm", goal="g",
            player_goal="g", ai_goal="g", player_stance="s", ai_stance="s",
            background="b",
        )
        text = recent_history_text(state)
        assert "no previous" in text.lower()
