"""Task modules; llm_do patched."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from schemas import (
    ConversationAnalysis,
    InitialEmotions,
    OpponentPersonalityAnalysis,
    ParseSetupResponse,
    SessionState,
)


# parse_setup

class TestParseSetup:
    @patch("tasks.parse_setup.llm_do")
    def test_returns_structured(self, mock_llm):
        mock_llm.return_value = ParseSetupResponse(
            background="Alice and Bob argue about rent.",
            ai_personality="defensive",
            goal="persuasion",
            player_goal="persuasion",
            ai_goal="persuasion",
            player_stance="Rent is too high.",
            ai_stance="Rent is fair.",
            relationship="roommates",
            player_role="tenant",
            ai_role="landlord",
        )
        from tasks.parse_setup import parse_background
        result = parse_background("Alice", "Bob", "roommates", "We argue about rent")
        assert result.ai_personality == "defensive"
        assert result.relationship == "roommates"
        mock_llm.assert_called_once()

    @patch("tasks.parse_setup.llm_do", side_effect=Exception("LLM down"))
    def test_fallback_on_failure(self, mock_llm):
        from tasks.parse_setup import parse_background
        result = parse_background("Alice", "Bob", "roommates", "We argue about rent")
        assert result.ai_personality == "defensive"
        assert result.goal == "persuasion"

    def test_empty_background_no_llm(self):
        from tasks.parse_setup import parse_background
        result = parse_background("Alice", "Bob", "roommates", "")
        assert result.background == "No background provided."


# infer_initial_emotions

class TestInferInitialEmotions:
    @patch("tasks.infer_initial_emotions.llm_do")
    def test_returns_emotions(self, mock_llm, sample_state: SessionState):
        mock_llm.return_value = InitialEmotions(player_emotion="angry", ai_emotion="anxious")
        from tasks.infer_initial_emotions import infer_initial_emotions
        p, a = infer_initial_emotions(sample_state)
        assert p == "angry"
        assert a == "anxious"

    @patch("tasks.infer_initial_emotions.llm_do", side_effect=Exception("fail"))
    def test_fallback_neutral(self, mock_llm, sample_state: SessionState):
        from tasks.infer_initial_emotions import infer_initial_emotions
        p, a = infer_initial_emotions(sample_state)
        assert p == "neutral"
        assert a == "neutral"


# analyze_conversation

class TestAnalyzeConversation:
    @patch("tasks.analyze_conversation.llm_do")
    def test_returns_analysis(self, mock_llm, sample_state: SessionState):
        mock_llm.return_value = ConversationAnalysis(
            player_emotion="angry",
            ai_emotion="neutral",
            toxicity=0.5,
            repetition_score=0.2,
            goal_reached=False,
            off_topic_score=0.1,
            player_goal_progress=0.3,
            ai_goal_progress=0.4,
        )
        from tasks.analyze_conversation import analyze_conversation_state
        result = analyze_conversation_state(sample_state)
        assert result["toxicity"] == 0.5
        assert result["player_emotion"] == "angry"

    @patch("tasks.analyze_conversation.llm_do", side_effect=Exception("fail"))
    def test_fallback(self, mock_llm, sample_state: SessionState):
        from tasks.analyze_conversation import analyze_conversation_state
        result = analyze_conversation_state(sample_state)
        assert result["player_emotion"] == "neutral"
        assert result["toxicity"] == 0.15


# infer_opponent_personality

class TestInferOpponentPersonality:
    @patch("tasks.infer_opponent_personality.llm_do")
    def test_returns_traits(self, mock_llm):
        mock_llm.return_value = OpponentPersonalityAnalysis(
            opponent_traits=["aggressive", "terse"],
            opponent_avg_message_length=8.0,
            strategy_notes=["Stay firm."],
        )
        from tasks.infer_opponent_personality import infer_opponent_personality
        result = infer_opponent_personality("Human: shut up", "shut up")
        assert "aggressive" in result["opponent_traits"]
        assert result["opponent_avg_message_length"] == 8.0

    @patch("tasks.infer_opponent_personality.llm_do", side_effect=Exception("fail"))
    def test_fallback(self, mock_llm):
        from tasks.infer_opponent_personality import infer_opponent_personality
        result = infer_opponent_personality("hi", "hi")
        assert result["opponent_traits"] == ["neutral"]
