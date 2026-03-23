# Extending RAG

## Built-in corpus

The system ships with the NSW *Residential Tenancies Act 2010* (`documents/act-2010-042.pdf`), indexed via `build_index.py`. This is the default corpus when no `corpus_ids` are specified.

## Multi-corpus retrieval

`search_documents(query, corpus_ids=None, top_k=5)` is the single retrieval function used by both agents. When multiple `corpus_ids` are supplied, system corpora are searched first — their results appear before user-uploaded results, giving them priority.

## Adding more system documents

Any text-based PDF can be indexed using `build_index.py`:

| Kind | Examples |
|------|----------|
| **Subordinate legislation** | Regulations or instruments under the Act |
| **Tribunal guidance** | Consumer/fair-trading fact sheets and guides |
| **Other jurisdictions** | Other states' residential tenancy Acts |

Each document gets its own Chroma collection.

## User-uploaded documents (policies, handbooks, etc.)

The backend exposes three endpoints for document management:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload_document` | POST | Upload a PDF → index into ChromaDB → returns `corpus_id` |
| `/attach_rag_corpus` | POST | JSON `{ "session_id", "corpus_id" }` — bind upload to session |
| `/corpora` | GET | List all indexed collections (system + uploaded) |
| `/corpora/{corpus_id}` | DELETE | Remove an indexed collection |

### Upload flow

1. Unity client uses **Runtime File Browser** to let the user pick a PDF.
2. Client sends the file via `POST /upload_document` (multipart form).
3. Backend saves to `rag/uploads/`, chunks with sliding window (1400 chars, 200 overlap), embeds, and stores in a dedicated Chroma collection.
4. Backend returns `{ "ok": true, "corpus_id": "upload_policy_local_abc12345" }`.
5. Client calls **`POST /attach_rag_corpus`** with that `corpus_id` and the current `session_id` (Unity does this after upload). Alternatively, pass **`rag_corpus_id`** on **`POST /init_session`** if the PDF was uploaded before the match started.
6. During each arguer turn, the orchestrator sets a **corpus scope**: **general** mode searches **only** session `rag_corpora` when non-empty (no stray NSW hits); **law** mode searches **NSW default first**, then session uploads. Chunk citations include **source label and page numbers** from indexer metadata.

### Priority rule

When **law** mode includes both the built-in statute index and uploads, **statute results are listed first** in the merged `search_documents` output. The agent should ground claims in retrieved text.

### Not yet implemented

- Multi-tenant access control
- OCR for scanned PDFs
- Table-aware chunking
