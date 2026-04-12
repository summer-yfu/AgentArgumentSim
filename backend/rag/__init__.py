"""Chroma RAG. chromadb loads lazily via __getattr__ so light imports stay cheap."""

from __future__ import annotations

from typing import Any

from rag.corpus_resolution import effective_corpus_ids_for_session

__all__ = [
    "collection_name_for_upload",
    "default_collection_name",
    "delete_collection",
    "effective_corpus_ids_for_session",
    "index_uploaded_pdf",
    "list_collections",
    "search_documents",
]


def __getattr__(name: str) -> Any:
    if name == "collection_name_for_upload":
        from rag.indexer import collection_name_for_upload

        return collection_name_for_upload
    if name == "delete_collection":
        from rag.indexer import delete_collection

        return delete_collection
    if name == "index_uploaded_pdf":
        from rag.indexer import index_uploaded_pdf

        return index_uploaded_pdf
    if name == "default_collection_name":
        from rag.retriever import default_collection_name

        return default_collection_name
    if name == "list_collections":
        from rag.retriever import list_collections

        return list_collections
    if name == "search_documents":
        from rag.retriever import search_documents

        return search_documents
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
