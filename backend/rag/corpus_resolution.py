"""Which corpus ids to pass into search for this session/mode."""

from __future__ import annotations


def effective_corpus_ids_for_session(
    rag_corpora: list[str],
    setup_mode: str,
    *,
    law_default_collection: str,
) -> list[str] | None:
    if not rag_corpora:
        return None
    mode = (setup_mode or "general").strip().lower()
    cleaned = list(dict.fromkeys(c.strip() for c in rag_corpora if c and str(c).strip()))
    if not cleaned:
        return None
    if mode == "law":
        d = (law_default_collection or "").strip()
        if not d:
            return cleaned
        return list(dict.fromkeys([d, *cleaned]))
    return cleaned
