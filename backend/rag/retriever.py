"""Query Chroma collections; format hits with section/page labels."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import chromadb
from connectonion import xray

from rag.context import get_scoped_rag_corpora

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
CHROMA_DIR = ROOT / "law_db"
UPLOADS_DIR = ROOT / "uploads"
PDF_PATH = ROOT / "documents" / "act-2010-042.pdf"
BASE_COLLECTION_NAME = "nsw_residential_tenancies"


def _sha8(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()[:8]


def _embedding_mode() -> str:
    use_local = os.environ.get("USE_LOCAL_EMBEDDINGS", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if use_local:
        return "local"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "local"


def default_collection_name() -> str:
    return f"{BASE_COLLECTION_NAME}_{_embedding_mode()}_{_sha8(PDF_PATH)}"


def _get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def _get_collection(collection_name: str | None = None):
    client = _get_client()
    name = collection_name or default_collection_name()

    if _embedding_mode() == "local":
        return client.get_collection(name)

    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-small",
    )
    return client.get_collection(name, embedding_function=embedding_fn)


def list_collections() -> list[str]:
    """Return names of all indexed collections."""
    client = _get_client()
    return [c.name for c in client.list_collections()]


@xray
def search_documents(query: str, corpus_ids: list[str] | None = None, top_k: int = 5) -> str:
    scoped = get_scoped_rag_corpora()
    if (corpus_ids is None or corpus_ids == []) and scoped is not None:
        corpus_ids = list(scoped)
    if not corpus_ids:
        corpus_ids = [default_collection_name()]

    all_chunks: list[str] = []
    for corpus_id in corpus_ids:
        try:
            collection = _get_collection(corpus_id)
        except Exception as exc:
            log.warning("Collection %s unavailable: %s", corpus_id, exc)
            all_chunks.append(f"[RAG_UNAVAILABLE: {corpus_id}] {exc}")
            continue

        result = collection.query(query_texts=[query], n_results=top_k)
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]

        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            section = meta.get("section", "unknown section")
            page_start = meta.get("page_start", "?")
            page_end = meta.get("page_end", "?")
            source = meta.get("source", corpus_id)
            citation = f"[{source} | {section}; pages {page_start}-{page_end}]"
            all_chunks.append(f"{citation}\n{doc}")

    if not all_chunks:
        return "No relevant document excerpts were found."

    xray.trace()
    return "\n\n---\n\n".join(all_chunks)
