"""Tool functions."""

from __future__ import annotations

import pytest

import tools.strategy as strategy_mod
from tools.strategy import (
    decide_next_move,
    suggest_loop_breaking_strategies,
    update_stance,
)
from tools.validation import validate_response
from tools.legal import detect_legal_topics
from tools.health import check_conversation_health, player_wants_to_stop


@pytest.fixture(autouse=True)
def _offline_stance_llm(monkeypatch):
    """Patch stance LLM so tests stay offline."""

    def _fake(**kwargs):
        return strategy_mod._fallback_revised_stance(kwargs["basis_stance"], kwargs["stance_action"])

    monkeypatch.setattr(strategy_mod, "revise_stance_with_llm", _fake)


# update_stance

class TestUpdateStance:
    def test_high_stubbornness_holds(self):
        result = update_stance("my stance", "defensive", 0.85, 5)
        assert result["stance_action"] == "hold"
        assert result["basis_stance"] == "my stance"
        assert result["revised_stance"] == "my stance"

    def test_low_stubbornness_softens_after_enough_rounds(self):
        result = update_stance("my stance", "calm", 0.2, 5, player_goal_progress=0.6)
        assert result["stance_action"] == "soften"
        assert result["revised_stance"].startswith("my stance")
        assert "still not abandoning" in result["revised_stance"]
        assert result["revised_stance"] != "my stance"

    def test_stubborn_personality_overrides_soften(self):
        result = update_stance("my stance", "stubborn", 0.3, 5, player_goal_progress=0.6)
        assert result["stance_action"] == "hold"
        assert result["revised_stance"] == "my stance"

    def test_aggressive_opponent_prevents_soften(self):
        result = update_stance("my stance", "calm", 0.3, 5, opponent_traits=["aggressive"], player_goal_progress=0.6)
        assert result["stance_action"] == "hold"
        assert result["revised_stance"] == "my stance"

    def test_narrow_returns_first_sentence(self):
        text = "Rent must reflect real costs. The timing was still unfair."
        result = update_stance(text, "calm", 0.5, 6, player_goal_progress=0.6)
        assert result["stance_action"] == "narrow"
        assert result["revised_stance"] == "Rent must reflect real costs."

    def test_returns_guidance(self):
        result = update_stance("my stance", "calm", 0.5, 2)
        assert "guidance" in result
        assert isinstance(result["guidance"], str)
        assert "revised_stance" in result
        assert result["revised_stance"] == "my stance"


# ── decide_next_move ──

class TestDecideNextMove:
    def test_very_high_stubbornness_early(self):
        result = decide_next_move(round_=2, stubbornness=0.9, personality="stubborn")
        assert result["main_move"] == "defend"
        assert result["tone"] == "firm"
        assert result["should_concede"] is False

    def test_low_stubbornness_late_allows_concession(self):
        result = decide_next_move(round_=5, stubbornness=0.2, personality="calm")
        assert result["should_concede"] is True
        assert result["should_offer_compromise"] is True

    def test_high_repetition_triggers_reframe(self):
        result = decide_next_move(round_=3, stubbornness=0.5, personality="logical", repetition_score=0.7)
        assert result["main_move"] == "reframe"

    def test_emotional_personality(self):
        result = decide_next_move(round_=3, stubbornness=0.5, personality="emotional")
        assert result["tone"] == "reactive"

    def test_returns_all_fields(self):
        result = decide_next_move(round_=1, stubbornness=0.5, personality="calm")
        expected_keys = {"main_move", "secondary_move", "tone", "should_concede", "should_offer_compromise",
                         "should_set_boundary", "prohibited_moves", "avoid_phrases", "reply_style", "reason"}
        assert expected_keys <= set(result.keys())


# suggest_loop_breaking_strategies

class TestSuggestLoopBreaking:
    def test_low_repetition_no_break(self):
        result = suggest_loop_breaking_strategies(0.3)
        assert result["needs_loop_break"] is False

    def test_high_repetition_triggers_break(self):
        result = suggest_loop_breaking_strategies(0.8)
        assert result["needs_loop_break"] is True
        assert result["recommended_move"] != "none"

    def test_reframe_after_question(self):
        result = suggest_loop_breaking_strategies(0.8, last_main_move="question")
        assert result["recommended_move"] == "reframe"


# ── detect_legal_topics ──

class TestDetectLegalTopics:
    def test_general_mode_skips(self):
        result = detect_legal_topics("Can you evict me?", setup_mode="general")
        assert result["should_search"] is False

    def test_law_mode_detects_eviction(self):
        result = detect_legal_topics("Can you evict me without notice?", setup_mode="law")
        assert result["should_search"] is True
        assert "evict" in result["query"]

    def test_law_mode_detects_general_law_reference(self):
        result = detect_legal_topics("I'm sure law wouldn't allow you to do that", setup_mode="law")
        assert result["should_search"] is True
        assert "law" in result["query"]

    def test_law_mode_detects_rights(self):
        result = detect_legal_topics("I know my rights here", setup_mode="law")
        assert result["should_search"] is True

    def test_law_mode_no_match(self):
        result = detect_legal_topics("I like pizza", setup_mode="law")
        assert result["should_search"] is False


# validate_response

class TestValidateResponse:
    def test_valid_reply(self):
        result = validate_response("That's not how I see it.", "human: blah\nai: stuff")
        assert result["valid"] is True

    def test_empty_reply(self):
        result = validate_response("", "some history")
        assert result["valid"] is False
        assert "empty_reply" in result["violations"]

    def test_too_long(self):
        long_reply = " ".join(["word"] * 80)
        result = validate_response(long_reply, "history")
        assert "too_long" in result["violations"]

    def test_meta_leak(self):
        result = validate_response("As an AI, I cannot do that.", "history")
        assert "meta_or_ooc" in result["violations"]

    def test_task_completed_phrase(self):
        result = validate_response("Task completed.", "history")
        assert result["valid"] is False
        assert "assistant_task_meta" in result["violations"]

    def test_task_completed_embedded(self):
        result = validate_response("Here's the proof. Task completed.", "history")
        assert "assistant_task_meta" in result["violations"]

    def test_policy_in_debate_allowed(self):
        """In-character "policy" is allowed."""
        result = validate_response(
            "HDR and undergrads aren't under the same policy, and that's intentional.",
            "history",
        )
        assert result["valid"] is True

    def test_banned_phrases(self):
        result = validate_response("I understand your point.", "history")
        assert "assistant_style_phrase" in result["violations"]

    def test_unsupported_legal_claim(self):
        result = validate_response("Under NSW law, you must give 90 days.", "history", setup_mode="law", used_legal_evidence=False)
        assert "unsupported_legal_claim" in result["violations"]

    def test_legal_claim_with_evidence_ok(self):
        result = validate_response("Under NSW law, you must give 90 days.", "history", setup_mode="law", used_legal_evidence=True)
        assert "unsupported_legal_claim" not in result["violations"]


# player_wants_to_stop

class TestPlayerWantsToStop:
    def test_detects_game_over(self):
        assert player_wants_to_stop("game over") is True

    def test_detects_lets_stop(self):
        assert player_wants_to_stop("let's stop here") is True

    def test_ignores_short_text(self):
        assert player_wants_to_stop("hi") is False

    def test_ignores_normal_message(self):
        assert player_wants_to_stop("I disagree with what you said") is False

    def test_case_insensitive(self):
        assert player_wants_to_stop("GAME OVER") is True

    def test_embedded_phrase(self):
        assert player_wants_to_stop("okay I think let's stop here, this is pointless") is True


# check_conversation_health

class TestCheckConversationHealth:
    def test_healthy(self):
        result = check_conversation_health(0.1, 0.1, 0.1, 3, False)
        assert result["recommended_action"] == "no_action"

    def test_toxicity_critical(self):
        result = check_conversation_health(0.95, 0.1, 0.1, 5, False)
        assert result["recommended_action"] == "toxicity_stop"
        assert result["toxicity_zone"] == "critical"

    def test_goal_reached(self):
        result = check_conversation_health(0.1, 0.1, 0.1, 5, True)
        assert result["recommended_action"] == "game_end"

    def test_max_rounds(self):
        result = check_conversation_health(0.1, 0.1, 0.1, 30, False)
        assert result["recommended_action"] == "game_end"

    def test_repetition_warning(self):
        result = check_conversation_health(0.1, 0.85, 0.1, 5, False)
        assert result["recommended_action"] == "repetition_warning"

    def test_off_topic(self):
        result = check_conversation_health(0.1, 0.1, 0.8, 3, False)
        assert result["recommended_action"] == "off_topic"
