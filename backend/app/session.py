from __future__ import annotations

from schemas import SessionState
from tasks.infer_initial_emotions import infer_initial_emotions

SESSIONS: dict[str, SessionState] = {}


def init_session(
    *,
    session_id: str,
    player_name: str,
    ai_name: str = "",
    relationship: str = "",
    player_role: str = "",
    ai_role: str = "",
    ai_personality: str = "",
    goal: str = "",
    player_goal: str = "",
    ai_goal: str = "",
    player_stance: str = "",
    ai_stance: str = "",
    background: str = "",
    setup_mode: str = "",
    rag_corpora: list[str] | None = None,
) -> SessionState:
    resolved_ai_goal = ai_goal or goal or "persuasion"
    resolved_player_goal = player_goal or goal or "persuasion"
    corpora = list(dict.fromkeys(c for c in (rag_corpora or []) if (c or "").strip()))
    state = SessionState(
        session_id=session_id,
        player_name=player_name or "Player",
        ai_name=ai_name or "AI",
        relationship=relationship or "unknown",
        player_role=player_role or "",
        ai_role=ai_role or "",
        ai_personality=ai_personality or "defensive",
        goal=resolved_ai_goal,
        player_goal=resolved_player_goal,
        ai_goal=resolved_ai_goal,
        player_stance=player_stance or "The current behavior or situation is not acceptable.",
        ai_stance=ai_stance or "The current behavior or situation is acceptable or justified.",
        background=background or "No background provided.",
        setup_mode=setup_mode or "general",
        rag_corpora=corpora,
    )
    player_emotion, ai_emotion = infer_initial_emotions(state)
    state.player_emotion = player_emotion
    state.ai_emotion = ai_emotion
    SESSIONS[session_id] = state
    return state


def get_session(session_id: str) -> SessionState:
    if session_id not in SESSIONS:
        raise KeyError(f"Unknown session_id: {session_id}")
    return SESSIONS[session_id]


def count_rounds(state: SessionState) -> int:
    return sum(1 for item in state.history if item.get("speaker") == "human")


def attach_rag_corpus(session_id: str, corpus_id: str) -> list[str]:
    state = get_session(session_id)
    cid = (corpus_id or "").strip()
    if not cid:
        raise ValueError("corpus_id is required")
    if cid not in state.rag_corpora:
        state.rag_corpora.append(cid)
    return list(state.rag_corpora)
