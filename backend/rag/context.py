"""ContextVar: active RAG corpus list for the current arguer turn."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_rag_corpus_ids: ContextVar[list[str] | None] = ContextVar("rag_corpus_ids", default=None)


@contextmanager
def rag_corpora_scope(corpus_ids: list[str] | None) -> Iterator[None]:
    token = _rag_corpus_ids.set(corpus_ids)
    try:
        yield
    finally:
        _rag_corpus_ids.reset(token)


def get_scoped_rag_corpora() -> list[str] | None:
    return _rag_corpus_ids.get()
