#!/usr/bin/env python3
from __future__ import annotations

"""CLI: index NSW Residential Tenancies Act PDF into Chroma."""

import argparse
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_PDF = ROOT / "documents" / "act-2010-042.pdf"
CHROMA_DIR = ROOT / "law_db"
BASE_COLLECTION_NAME = "nsw_residential_tenancies"

PART_RE = re.compile(r"^Part\s+\d+[A-Z]?\b.*", re.IGNORECASE)
DIVISION_RE = re.compile(r"^Division\s+\d+[A-Z]?\b.*", re.IGNORECASE)
SECTION_RE = re.compile(r"^\d+[A-Z]?\s+.+")
SCHEDULE_RE = re.compile(r"^Schedule\s+\d+[A-Z]?\b.*", re.IGNORECASE)

MAX_CHARS = 1400
OVERLAP_CHARS = 200


@dataclass
class LawBlock:
    text: str
    page_start: int
    page_end: int
    part: str
    division: str
    section: str


def sha8(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()[:8]


def clean_line(line: str) -> str:
    return re.sub(r"[ \t]+", " ", line).strip()


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    if re.match(r"^--\s*\d+\s*of\s*\d+\s*--$", line):
        return True
    if re.match(r"^Page\s+\d+\s+of\s+\d+$", line):
        return True
    if "Current version for" in line and "Page" in line:
        return True
    return False


def extract_pages(pdf_path: Path) -> list[tuple[int, list[str]]]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, list[str]]] = []

    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        lines = [clean_line(x) for x in raw.splitlines()]
        lines = [x for x in lines if not is_noise_line(x)]
        if lines:
            pages.append((i + 1, lines))

    return pages


def extract_blocks(pages: list[tuple[int, list[str]]]) -> list[LawBlock]:
    blocks: list[LawBlock] = []

    current_part = ""
    current_division = ""
    current_section = ""
    current_lines: list[str] = []
    current_page_start = None
    current_page_end = None

    def flush():
        nonlocal current_lines, current_page_start, current_page_end
        if (
            current_lines
            and current_page_start is not None
            and current_page_end is not None
        ):
            text = "\n".join(current_lines).strip()
            if text:
                blocks.append(
                    LawBlock(
                        text=text,
                        page_start=current_page_start,
                        page_end=current_page_end,
                        part=current_part,
                        division=current_division,
                        section=current_section,
                    )
                )
        current_lines = []
        current_page_start = None
        current_page_end = None

    for page_no, lines in pages:
        for line in lines:
            if PART_RE.match(line):
                current_part = line
                continue
            if DIVISION_RE.match(line):
                current_division = line
                continue
            if SCHEDULE_RE.match(line):
                flush()
                current_division = ""
                current_section = line
                current_lines = [line]
                current_page_start = page_no
                current_page_end = page_no
                continue
            if SECTION_RE.match(line):
                flush()
                current_section = line
                current_lines = [line]
                current_page_start = page_no
                current_page_end = page_no
                continue

            if current_page_start is None:
                current_page_start = page_no
            current_page_end = page_no
            current_lines.append(line)

    flush()
    return blocks


def split_large_block(
    block: LawBlock,
    max_chars: int = MAX_CHARS,
    overlap: int = OVERLAP_CHARS,
) -> list[LawBlock]:
    text = block.text
    if len(text) <= max_chars:
        return [block]

    pieces: list[LawBlock] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        piece_text = text[start:end].strip()
        if piece_text:
            pieces.append(
                LawBlock(
                    text=piece_text,
                    page_start=block.page_start,
                    page_end=block.page_end,
                    part=block.part,
                    division=block.division,
                    section=block.section,
                )
            )
        if end == len(text):
            break
        start = max(0, end - overlap)

    return pieces


def to_documents(blocks: list[LawBlock]) -> tuple[list[str], list[dict], list[str]]:
    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    idx = 0
    for block in blocks:
        for piece_idx, piece in enumerate(split_large_block(block)):
            prefix_parts = [x for x in [piece.part, piece.division, piece.section] if x]
            prefix = " | ".join(prefix_parts)
            full_text = f"{prefix}\n\n{piece.text}" if prefix else piece.text

            documents.append(full_text)
            metadatas.append(
                {
                    "source": "Residential Tenancies Act 2010 No 42",
                    "page_start": piece.page_start,
                    "page_end": piece.page_end,
                    "part": piece.part,
                    "division": piece.division,
                    "section": piece.section,
                    "piece_index": piece_idx,
                }
            )
            ids.append(f"rta2010_{idx}")
            idx += 1

    return documents, metadatas, ids


def get_collection(client, collection_name: str, mode: str):
    if mode == "local":
        return client.get_or_create_collection(name=collection_name)

    if mode == "openai":
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for --openai mode")

        embedding_fn = OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small",
        )
        return client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn,
        )

    raise ValueError(f"Unknown mode: {mode}")


def build_index(pdf_path: Path, mode: str, rebuild: bool) -> None:
    import chromadb

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_key = sha8(pdf_path)
    collection_name = f"{BASE_COLLECTION_NAME}_{mode}_{pdf_key}"

    print(f"Reading PDF: {pdf_path}")
    pages = extract_pages(pdf_path)
    if not pages:
        raise ValueError("No text extracted from PDF")

    print(f"Extracted pages: {len(pages)}")

    blocks = extract_blocks(pages)
    print(f"Structured blocks: {len(blocks)}")

    documents, metadatas, ids = to_documents(blocks)
    print(f"Final chunks: {len(documents)}")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if rebuild:
        try:
            client.delete_collection(collection_name)
            print(f"Deleted old collection: {collection_name}")
        except Exception:
            pass

    collection = get_collection(client, collection_name, mode)
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    print(f"Saved to: {CHROMA_DIR}")
    print(f"Collection: {collection_name}")
    print(f"Embedding mode: {mode}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--rebuild", action="store_true")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--local", action="store_true")
    mode_group.add_argument("--openai", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    mode = "openai" if args.openai else "local"
    build_index(args.pdf, mode, args.rebuild)
