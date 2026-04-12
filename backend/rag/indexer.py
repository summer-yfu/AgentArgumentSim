"""Index uploaded PDFs into Chroma (chunking aligned with build_index)."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path

import chromadb

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
CHROMA_DIR = ROOT / "law_db"
UPLOADS_DIR = ROOT / "uploads"

MAX_CHARS = 1400
OVERLAP_CHARS = 200


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
        "1", "true", "yes",
    )
    if use_local:
        return "local"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "local"


def _get_or_create_collection(client: chromadb.ClientAPI, name: str):
    mode = _embedding_mode()
    if mode == "local":
        return client.get_or_create_collection(name=name)

    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-small",
    )
    return client.get_or_create_collection(name=name, embedding_function=embedding_fn)


def _extract_text_from_pdf(pdf_path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, page_text), ...] from a PDF."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i + 1, text))
    return pages


def _sliding_window_chunks(
    text: str,
    max_chars: int = MAX_CHARS,
    overlap: int = OVERLAP_CHARS,
) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def collection_name_for_upload(filename: str, file_hash: str) -> str:
    """Deterministic collection name for an uploaded file."""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(filename).stem)[:40]
    mode = _embedding_mode()
    return f"upload_{safe}_{mode}_{file_hash}"


def index_uploaded_pdf(pdf_path: Path, source_label: str = "") -> str:
    """Index a user-uploaded PDF into a dedicated Chroma collection.

    Returns the collection name (corpus_id) used for retrieval.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    file_hash = _sha8(pdf_path)
    col_name = collection_name_for_upload(pdf_path.name, file_hash)
    source = source_label or pdf_path.stem

    pages = _extract_text_from_pdf(pdf_path)
    if not pages:
        raise ValueError(f"No text could be extracted from {pdf_path}")

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    idx = 0
    for page_no, page_text in pages:
        for chunk in _sliding_window_chunks(page_text):
            documents.append(chunk)
            metadatas.append({
                "source": source,
                "page_start": page_no,
                "page_end": page_no,
                "section": f"page {page_no}",
                "type": "user_upload",
            })
            ids.append(f"{col_name}_{idx}")
            idx += 1

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = _get_or_create_collection(client, col_name)
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    log.info("Indexed %d chunks from %s -> collection=%s", len(documents), pdf_path.name, col_name)
    return col_name


def delete_collection(collection_name: str) -> bool:
    """Remove an indexed collection. Returns True if deleted."""
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        client.delete_collection(collection_name)
        log.info("Deleted collection: %s", collection_name)
        return True
    except Exception as exc:
        log.warning("Could not delete collection %s: %s", collection_name, exc)
        return False
