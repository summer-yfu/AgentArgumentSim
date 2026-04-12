# Argument Agent

Real-time **human vs AI argument** simulation: ConnectOnion agents (arguer + mediator), FastAPI backend, optional **RAG** (NSW tenancy law + uploaded PDFs), **Unity** client under `frontend/argument_sim/`.

Uses [ConnectOnion](https://docs.connectonion.com) for agents, tools, and auth.

## Project structure

```
argument_agent/
├── backend/                        # Python backend
│   ├── agents/                     # ConnectOnion Agent instances (arguer, mediator) + hooks
│   │   ├── arguer.py
│   │   ├── mediator.py
│   │   └── _hooks.py               # log each LLM iteration → .co/logs/iterations.jsonl
│   ├── app/                        # FastAPI app: routes, run_turn pipeline, in-memory sessions
│   │   ├── server.py               # HTTP endpoints
│   │   ├── orchestrator.py         # arguer → post-turn analysis → mediator gate
│   │   └── session.py              # SessionState store, attach RAG corpus ids
│   ├── cli/                        # Terminal debate UI (no Unity)
│   │   ├── __main__.py             # python -m cli
│   │   └── debate.py               # interactive TUI
│   ├── config/                     # thresholds, banned phrases, stop phrases, emotion allow-list
│   │   └── constants.py
│   ├── factcheck/                  # optional fact-check agent (ConnectOnion host/connect)
│   │   ├── agent.py                # builds the factcheck Agent with web + RAG tools
│   │   ├── checker.py              # client: connect to hosted factcheck agent
│   │   ├── server.py               # python -m factcheck.server
│   │   └── prompts/factcheck.md
│   ├── prompts/                    # markdown prompts loaded at runtime
│   │   ├── agents/                 # system prompts for arguer + mediator
│   │   └── tasks/                  # prompts for structured llm_do tasks
│   ├── rag/                        # Chroma RAG: index PDFs, query, session corpus resolution
│   │   ├── build_index.py          # CLI: index default NSW Act
│   │   ├── indexer.py              # upload PDF → chunks → collection
│   │   ├── retriever.py            # search_documents, list/delete collections
│   │   ├── corpus_resolution.py    # which corpus ids for law vs general + uploads
│   │   ├── context.py              # ContextVar scope for active corpora per arguer turn
│   │   ├── documents/              # bundled statute PDF for default index
│   │   ├── law_db/                 # Chroma on-disk store (gitignored)
│   │   └── uploads/                # saved upload PDFs (gitignored)
│   ├── schemas/                    # Pydantic: API bodies, SessionState, LLM output shapes
│   ├── tasks/                      # llm_do: parse setup, analyze turn, emotions, stance, personality
│   ├── tools/                      # @tool callables: strategy, validate reply, legal regex, health
│   │   ├── strategy.py             # stance, opponent read, moves, loop hints
│   │   ├── validation.py
│   │   ├── legal.py
│   │   └── health.py
│   └── utils/                      # helpers (history text, clamp) + agent tool-message parsing
│
├── frontend/                       # Client applications
│   └── argument_sim/               # Unity client: setup UI + chat → backend API
│
├── tests/                          # pytest (tools, tasks, API, session, RAG resolution)
│   ├── conftest.py
│   └── test_*.py
│
├── data/                           # Runtime data (gitignored)
│   └── chathistory/
│
├── main.py                         # uvicorn entry, load_dotenv, adds backend/ to sys.path
├── setup.sh
├── requirements.txt
├── requirements-browser.txt
├── pytest.ini
├── .env.example
├── .co/                            # ConnectOnion project (co init); logs/evals gitignored
└── .gitignore
```

## Quick start

```bash
git clone <your-repo-url> && cd argument_agent
bash setup.sh
source .venv/bin/activate
uvicorn main:app --reload --port 8191
```

## Manual setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
co init          # if you do not already have .co/config.toml
co auth
python backend/rag/build_index.py --local --rebuild
```

## To run the game

```bash
uvicorn main:app --reload --port 8191
```

Then open the built Unity game.

## CLI (terminal debate, no Unity)

Interactive setup mirrors the game (topic type, relationship, names, **free-form background** — no Ink step-by-step), then `parse_background` refines stances/roles. Confirm with Enter, then type turns in the terminal.

```bash
source .venv/bin/activate
PYTHONPATH=backend python -m cli
```

(`PYTHONPATH=backend python -m cli debate` is the same thing.)

Requires the same `.env` / `co auth` as the server (LLM calls run in-process).

## Features

- **Arguer agent** — Tools: stance, personality read, legal-topic hint, `search_documents`, move planning, `validate_response`
- **Mediator agent** — Intervenes when health signals warrant it
- **Structured tasks** — `llm_do` for setup parsing, emotions, conversation analysis, stance revision, opponent style
- **RAG** — Default statute index + per-session PDF corpora
- **Unity** — Setup flow and chat UI interface
- **Tests** — `pytest` with mocks for offline runs

## How it works

1. Client calls `/parse_setup`, `/init_session`, then `/turn` with human text.
2. Orchestrator builds state JSON, runs the arguer (`Agent.input`), runs analysis, optionally the mediator.
3. Session fields (history, stance, scores) update each turn.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/parse_setup` | Background text → structured setup |
| POST | `/init_session` | New session + initial emotions |
| POST | `/turn` | Human message → AI reply, analysis, optional mediator |
| POST | `/upload_document` | Index PDF → `corpus_id` |
| POST | `/attach_rag_corpus` | Attach corpus to session |
| GET | `/corpora` | List collections |
| DELETE | `/corpora/{id}` | Remove collection |

## RAG

- Session `setup_mode`: `general` vs `law`.
- Default index: NSW Residential Tenancies Act (`backend/rag/build_index.py`).
- Upload flow: `/upload_document` then `/attach_rag_corpus`.
- Law mode: default statute collection plus session corpora; general with uploads: attached corpora only.

## Environment

**What belongs in `.env`**

- **`OPENONION_API_KEY`**, **`AGENT_EMAIL`**, **`AGENT_ADDRESS`**, **`AGENT_CONFIG_PATH`** — OpenOnion / ConnectOnion identity and API access. Usually created or updated by **`co auth`**; you can also set them in `.env` so any library that reads the process environment sees them. This repo's Python code does not hard-code those names; they are for the ConnectOnion stack.
- **`OPENAI_API_KEY`** — Only if you built the Chroma index with OpenAI embeddings; must match runtime (`backend/rag/retriever.py`, `backend/rag/indexer.py`).
- **`USE_LOCAL_EMBEDDINGS`** — Optional. If set to `1` / `true` / `yes`, RAG uses local sentence-transformers mode. Yes, it is a normal environment variable; putting it in `.env` is fine.
- **`LOG_LEVEL`** — Optional. Sets Python's logging level for the API process (`DEBUG`, `INFO`, `WARNING`, …). `main.py` reads `os.environ["LOG_LEVEL"]` (default `INFO`). It only affects log verbosity, not model behavior.

**Loading `.env`**

`main.py` calls `python-dotenv`'s `load_dotenv()` once at import time. That copies variables from a `.env` file into **`os.environ`** for this process. Logging and RAG code read `os.environ`; ConnectOnion typically uses the same environment for API calls. It does not replace `co auth`'s on-disk config—it just ensures vars you put in `.env` are visible to the running server.

Use `.env.example` as a template. **Never commit** a real `.env` (your file contains secrets such as `OPENONION_API_KEY`).

## Unity

Open `frontend/argument_sim/` in Unity **2022.3 LTS+**. Target API base URL `http://127.0.0.1:8191`.

**Download chat history (built player):** files go under **`Application.persistentDataPath/chathistory/`** (e.g. macOS `~/Library/Application Support/<CompanyName>/<ProductName>/chathistory/`). The game logs the full path, copies it to the clipboard, and tries to open that folder in Explorer / Finder / xdg-open. In the Editor, **Reveal in Finder** is used instead.

## Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

Mocks replace `llm_do` / `Agent.input` where needed so tests stay offline and deterministic.

## Documentation

- [ConnectOnion](https://docs.connectonion.com)
