"""Pytest fixtures."""

from __future__ import annotations

import pytest

from schemas import SessionState


@pytest.fixture
def sample_state() -> SessionState:
    return SessionState(
        session_id="test-123",
        player_name="Alice",
        ai_name="Bob",
        relationship="roommates",
        player_role="tenant",
        ai_role="landlord",
        ai_personality="defensive",
        goal="persuasion",
        player_goal="persuasion",
        ai_goal="persuasion",
        player_stance="The rent increase is unreasonable.",
        ai_stance="The rent increase is fair and necessary.",
        background="Alice and Bob are roommates arguing about rent.",
        setup_mode="general",
        history=[
            {"speaker": "human", "text": "I think the rent is too high."},
            {"speaker": "ai", "text": "It reflects the current market."},
            {"speaker": "human", "text": "But we agreed on a fixed amount!"},
        ],
        player_emotion="angry",
        ai_emotion="neutral",
        toxicity=0.3,
        player_goal_progress=0.2,
        ai_goal_progress=0.4,
        repetition_score=0.1,
    )


@pytest.fixture
def law_state(sample_state: SessionState) -> SessionState:
    sample_state.setup_mode = "law"
    return sample_state
