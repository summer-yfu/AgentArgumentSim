"""HTTP routes; LLM patched."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from schemas import ParseSetupResponse


@pytest.fixture
def client():
    from app.server import app
    return TestClient(app)


class TestParseSetupEndpoint:
    @patch("tasks.parse_setup.llm_do")
    def test_parse_setup(self, mock_llm, client):
        mock_llm.return_value = ParseSetupResponse(
            background="Test background",
            ai_personality="calm",
            goal="persuasion",
            player_goal="persuasion",
            ai_goal="persuasion",
            player_stance="stance a",
            ai_stance="stance b",
            relationship="friends",
        )
        resp = client.post("/parse_setup", json={
            "player_name": "Alice",
            "relationship": "friends",
            "background": "We had a fight about dishes.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_personality"] == "calm"


class TestInitSessionEndpoint:
    @patch("tasks.infer_initial_emotions.llm_do")
    def test_init_session(self, mock_emotions, client):
        from schemas import InitialEmotions
        mock_emotions.return_value = InitialEmotions(player_emotion="angry", ai_emotion="neutral")
        resp = client.post("/init_session", json={
            "session_id": "test-session-api",
            "player_name": "Alice",
            "ai_name": "Bob",
            "relationship": "roommates",
            "ai_personality": "defensive",
            "player_goal": "persuasion",
            "ai_goal": "persuasion",
            "player_stance": "Rent too high",
            "ai_stance": "Rent is fair",
            "background": "Rent dispute",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["player_name"] == "Alice"
        assert data.get("rag_corpora") == []

    @patch("tasks.infer_initial_emotions.llm_do")
    def test_init_session_with_rag_corpus_id(self, mock_emotions, client):
        from schemas import InitialEmotions
        mock_emotions.return_value = InitialEmotions(player_emotion="neutral", ai_emotion="neutral")
        resp = client.post("/init_session", json={
            "session_id": "test-rag-init",
            "player_name": "Alice",
            "ai_name": "Bob",
            "relationship": "students",
            "ai_personality": "logical",
            "player_goal": "persuasion",
            "ai_goal": "persuasion",
            "player_stance": "x",
            "ai_stance": "y",
            "background": "policy debate",
            "rag_corpus_id": "upload_policy_local_abc12345",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "upload_policy_local_abc12345" in data.get("rag_corpora", [])


class TestAttachRagCorpus:
    @patch("tasks.infer_initial_emotions.llm_do")
    def test_attach_after_init(self, mock_emotions, client):
        from schemas import InitialEmotions
        mock_emotions.return_value = InitialEmotions(player_emotion="neutral", ai_emotion="neutral")
        client.post("/init_session", json={
            "session_id": "attach-test",
            "player_name": "A",
            "ai_name": "B",
            "ai_personality": "calm",
            "player_goal": "g",
            "ai_goal": "g",
            "player_stance": "x",
            "ai_stance": "y",
            "background": "b",
        })
        r = client.post("/attach_rag_corpus", json={
            "session_id": "attach-test",
            "corpus_id": "upload_doc_local_deadbeef",
        })
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert "upload_doc_local_deadbeef" in r.json()["rag_corpora"]

    def test_attach_unknown_session(self, client):
        r = client.post("/attach_rag_corpus", json={
            "session_id": "nope",
            "corpus_id": "x",
        })
        assert r.status_code == 404


class TestTurnEndpoint:
    @patch("tasks.infer_initial_emotions.llm_do")
    @patch("tasks.analyze_conversation.llm_do")
    @patch("connectonion.Agent.input", return_value="I disagree.")
    def test_turn_basic(self, mock_agent, mock_analysis, mock_emotions, client):
        from schemas import ConversationAnalysis, InitialEmotions
        mock_emotions.return_value = InitialEmotions(player_emotion="neutral", ai_emotion="neutral")
        mock_analysis.return_value = ConversationAnalysis(
            player_emotion="neutral", ai_emotion="neutral",
            toxicity=0.1, repetition_score=0.0, goal_reached=False,
            off_topic_score=0.0, player_goal_progress=0.1, ai_goal_progress=0.1,
        )

        client.post("/init_session", json={
            "session_id": "turn-test",
            "player_name": "Alice",
            "ai_name": "Bob",
            "ai_personality": "calm",
            "player_goal": "persuasion",
            "ai_goal": "persuasion",
            "player_stance": "x",
            "ai_stance": "y",
            "background": "test",
        })

        resp = client.post("/turn", json={
            "session_id": "turn-test",
            "human_input": "I think you're wrong.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["speaker"] == "ai"
        assert len(data["reply"]) > 0


# upload / corpora

class TestUploadEndpoint:
    def test_reject_non_pdf(self, client):
        resp = client.post(
            "/upload_document",
            files={"file": ("readme.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]

    @patch("app.server.index_uploaded_pdf", return_value="upload_test_local_abc12345")
    def test_upload_pdf(self, mock_index, client, tmp_path):
        fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
        resp = client.post(
            "/upload_document",
            files={"file": ("policy.pdf", fake_pdf, "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["corpus_id"] == "upload_test_local_abc12345"
        mock_index.assert_called_once()


class TestCorporaEndpoints:
    @patch("app.server.list_collections", return_value=["nsw_residential_tenancies_local_abc", "upload_dorm_local_def"])
    def test_list_corpora(self, mock_list, client):
        resp = client.get("/corpora")
        assert resp.status_code == 200
        assert len(resp.json()["corpora"]) == 2

    @patch("app.server.delete_collection", return_value=True)
    def test_delete_corpus(self, mock_del, client):
        resp = client.delete("/corpora/upload_test_local_abc")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    @patch("app.server.delete_collection", return_value=False)
    def test_delete_missing_corpus(self, mock_del, client):
        resp = client.delete("/corpora/nonexistent")
        assert resp.status_code == 404
