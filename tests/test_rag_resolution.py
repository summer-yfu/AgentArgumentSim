"""rag.corpus_resolution only."""

from __future__ import annotations

from rag.corpus_resolution import effective_corpus_ids_for_session


def test_no_uploads_returns_none():
    assert effective_corpus_ids_for_session([], "general", law_default_collection="nsw") is None
    assert effective_corpus_ids_for_session([], "law", law_default_collection="nsw") is None


def test_general_mode_only_user_corpora():
    out = effective_corpus_ids_for_session(
        ["upload_a", "upload_b"], "general", law_default_collection="nsw_default"
    )
    assert out == ["upload_a", "upload_b"]


def test_law_mode_prepends_default():
    out = effective_corpus_ids_for_session(["upload_a"], "law", law_default_collection="nsw_default")
    assert out == ["nsw_default", "upload_a"]


def test_law_mode_dedupes():
    out = effective_corpus_ids_for_session(
        ["nsw_default", "upload_a"], "law", law_default_collection="nsw_default"
    )
    assert out == ["nsw_default", "upload_a"]
