"""Session init and rounds."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from schemas import InitialEmotions


class TestSession:
    @patch("tasks.infer_initial_emotions.llm_do")
    def test_init_and_get(self, mock_llm):
        mock_llm.return_value = InitialEmotions(player_emotion="neutral", ai_emotion="neutral")
        from app.session import get_session, init_session
        init_session(
            session_id="sess-1",
            player_name="Alice",
            ai_name="Bob",
            relationship="roommates",
            ai_personality="calm",
            goal="persuasion",
            player_stance="x",
            ai_stance="y",
            background="test",
        )
        state = get_session("sess-1")
        assert state.player_name == "Alice"
        assert state.ai_personality == "calm"

    def test_unknown_session_raises(self):
        from app.session import get_session
        with pytest.raises(KeyError):
            get_session("nonexistent")

    @patch("tasks.infer_initial_emotions.llm_do")
    def test_count_rounds(self, mock_llm):
        mock_llm.return_value = InitialEmotions(player_emotion="neutral", ai_emotion="neutral")
        from app.session import count_rounds, init_session
        state = init_session(
            session_id="sess-rounds",
            player_name="A",
            background="b",
        )
        assert count_rounds(state) == 0
        state.history.append({"speaker": "human", "text": "hi"})
        state.history.append({"speaker": "ai", "text": "hello"})
        assert count_rounds(state) == 1
