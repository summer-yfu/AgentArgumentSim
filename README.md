<h1>Argument Agent <img src="assets/icon.png" width="36"></h1>

Real-time human vs AI argument simulation. Practice arguing with AI. Pick a topic, set up the scenario and AI personality, and go argue with a LLM agent. A mediator steps in if things go off the rails. Agent will change emotions during the argument.

Play in Unity (a slime guides you through setup) or straight from the terminal.

Built with three [ConnectOnion](https://docs.connectonion.com) agents (arguer, mediator, fact-checker), FastAPI, optional RAG, and a Unity client.

## Project structure

```
argument_agent/
├── backend/
│   ├── agents/          # AI arguer & mediator agents
│   ├── app/             # FastAPI server, orchestrator, sessions
│   ├── cli/             # Terminal debate mode
│   ├── factcheck/       # Optional AI fact-check agent
│   ├── prompts/         # System prompts (agents + tasks)
│   ├── rag/             # Chroma RAG (indexer, retriever, documents/)
│   ├── tools/           # Agent tools 
├── frontend/
│   └── argument_sim/    # Unity client
├── main.py              # uvicorn entry point
```

## Setup

```bash
python3 -m venv argumentsim && source argumentsim/bin/activate
pip install -r requirements.txt
co init && co auth
cp .env.example .env           # fill in your API keys
python backend/rag/build_index.py --local --rebuild  # building rag
```

<details>
<summary>Quick setup (one command)</summary>

```bash
bash setup.sh
```

</details>

## Run

1. Start the backend:

```bash
source argumentsim/bin/activate
uvicorn main:app --reload --port 8191
```

2. Open the Unity game (`frontend/argument_sim/`, built with Unity 2022.3 LTS). Don't have Unity installed? Ask me for a pre-built version.

**CLI mode**:

```bash
PYTHONPATH=backend python -m cli
```



## Customization

### Game flow 

The setup screen is driven by [Ink](https://www.inklestudios.com/ink/) — edit `frontend/argument_sim/Assets/dialogue/slime.ink` to change questions, choices, or flow order. The C# side (`InkSetupController.cs`) reads the Ink story and renders it; you only need to touch C# if you're changing UI behavior (e.g. adding new panels or animations).

### Agent behavior

To change how an agent argues, mediates, or fact-checks, edit the system prompts:

| What | File |
|------|------|
| Arguer personality & rules | `backend/prompts/agents/AI_arguer.md` |
| Mediator intervention style | `backend/prompts/agents/mediator.md` |
| Fact-check agent | `backend/factcheck/agent.py` + `backend/factcheck/prompts/factcheck.md` |

Task-level prompts (how the LLM parses setup, analyzes conversation, infers emotions, etc.) are in `backend/prompts/tasks/`.

To add a new agent, use `backend/factcheck/agent.py` as a reference — it shows how to define a ConnectOnion `Agent` with tools, a system prompt, and a `host()` entry point.

### Thresholds & constants

Toxicity limits, repetition thresholds, banned phrases, emotion allow-list, etc. are all in `backend/config/constants.py`.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/parse_setup` | Background text → structured setup |
| POST | `/init_session` | New session + initial emotions |
| POST | `/turn` | Human message → AI reply + analysis |
| POST | `/upload_document` | Index PDF → `corpus_id` |
| POST | `/attach_rag_corpus` | Attach corpus to session |
| GET | `/corpora` | List RAG collections |
| DELETE | `/corpora/{id}` | Remove collection |

## Environment

Copy `.env.example` to `.env`. Key variables:

- `OPENONION_API_KEY` — set by `co auth`
- `USE_LOCAL_EMBEDDINGS=1` — use local embeddings for RAG (default)
- `OPENAI_API_KEY` — only if using OpenAI embeddings
- `LOG_LEVEL` — optional (`DEBUG`, `INFO`, etc.)

