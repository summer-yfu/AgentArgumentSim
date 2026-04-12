import logging
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.orchestrator import run_turn
from app.session import attach_rag_corpus, get_session, init_session
from rag import delete_collection, index_uploaded_pdf, list_collections
from rag.indexer import UPLOADS_DIR
from schemas import (
    AttachRagCorpusRequest,
    AttachRagCorpusResponse,
    InitSessionRequest,
    InitSessionResponse,
    ParseSetupRequest,
    ParseSetupResponse,
    TurnRequest,
    TurnResponse,
)
from tasks.parse_setup import parse_background

log = logging.getLogger(__name__)

app = FastAPI(title="Argument Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/turn", response_model=TurnResponse)
def turn(req: TurnRequest):
    log.info("Turn session=%s input=%s", req.session_id, req.human_input[:80])
    from app.session import get_session as _get  # noqa: F811

    try:
        _get(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown session_id: {req.session_id}")

    try:
        result = run_turn(req.session_id, req.human_input)
    except Exception as exc:
        log.exception("Error in run_turn (session=%s)", req.session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return TurnResponse(**result)


@app.post("/init_session", response_model=InitSessionResponse)
def init_session_route(req: InitSessionRequest):
    has_personality = bool((req.ai_personality or "").strip())
    has_player_goal = bool((req.player_goal or req.goal or "").strip())
    has_ai_goal = bool((req.ai_goal or req.goal or "").strip())
    has_player_stance = bool((req.player_stance or "").strip())
    has_ai_stance = bool((req.ai_stance or "").strip())
    has_background = bool((req.background or "").strip())
    needs_parse = not (
        has_personality
        and has_player_goal
        and has_ai_goal
        and has_player_stance
        and has_ai_stance
        and has_background
    )

    if needs_parse:
        parsed = parse_background(
            player_name=req.player_name or "",
            ai_name=req.ai_name or "",
            relationship=req.relationship or "",
            background=req.background or "",
        )
    else:
        parsed = None

    background = req.background or (parsed.background if parsed else "") or "No background provided."

    merged_rag: list[str] = list(req.rag_corpora or [])
    rid = (req.rag_corpus_id or "").strip()
    if rid and rid not in merged_rag:
        merged_rag.append(rid)

    init_session(
        session_id=req.session_id,
        player_name=req.player_name,
        ai_name=req.ai_name or "",
        relationship=req.relationship or (parsed.relationship if parsed else "") or "unknown",
        player_role=req.player_role or (parsed.player_role if parsed else ""),
        ai_role=req.ai_role or (parsed.ai_role if parsed else ""),
        ai_personality=req.ai_personality or (parsed.ai_personality if parsed else "") or "defensive",
        goal=req.ai_goal or req.goal or (parsed.ai_goal if parsed else "") or (parsed.goal if parsed else "") or "persuasion",
        player_goal=req.player_goal or req.goal or (parsed.player_goal if parsed else "") or (parsed.goal if parsed else "") or "persuasion",
        ai_goal=req.ai_goal or req.goal or (parsed.ai_goal if parsed else "") or (parsed.goal if parsed else "") or "persuasion",
        player_stance=req.player_stance or (parsed.player_stance if parsed else "") or "The current behavior or situation is not acceptable.",
        ai_stance=req.ai_stance or (parsed.ai_stance if parsed else "") or "The current behavior or situation is acceptable or justified.",
        background=background,
        setup_mode=req.setup_mode or "general",
        rag_corpora=merged_rag,
    )
    state = get_session(req.session_id)

    return InitSessionResponse(
        ok=True,
        player_name=state.player_name,
        ai_name=state.ai_name,
        relationship=state.relationship,
        player_role=state.player_role,
        ai_role=state.ai_role,
        ai_personality=state.ai_personality,
        goal=state.goal,
        player_goal=state.player_goal,
        ai_goal=state.ai_goal,
        player_stance=state.player_stance,
        ai_stance=state.ai_stance,
        background=state.background,
        setup_mode=state.setup_mode,
        player_emotion=state.player_emotion,
        ai_emotion=state.ai_emotion,
        player_goal_progress=state.player_goal_progress,
        ai_goal_progress=state.ai_goal_progress,
        rag_corpora=state.rag_corpora,
    )


@app.post("/attach_rag_corpus", response_model=AttachRagCorpusResponse)
def attach_rag_corpus_route(body: AttachRagCorpusRequest):
    try:
        get_session(body.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown session_id: {body.session_id}") from None
    try:
        corpora = attach_rag_corpus(body.session_id, body.corpus_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AttachRagCorpusResponse(ok=True, rag_corpora=corpora)


@app.post("/parse_setup", response_model=ParseSetupResponse)
def parse_setup(req: ParseSetupRequest):
    return parse_background(
        player_name=req.player_name or "",
        ai_name=req.ai_name or "",
        relationship=req.relationship or "",
        background=req.background or "",
    )


@app.post("/upload_document")
def upload_document(file: UploadFile, source_label: str = ""):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        corpus_id = index_uploaded_pdf(dest, source_label=source_label or "")
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Indexing failed: {exc}") from exc

    log.info("Uploaded & indexed %s -> %s", file.filename, corpus_id)
    return {"ok": True, "corpus_id": corpus_id, "filename": file.filename}


@app.get("/corpora")
def get_corpora():
    return {"corpora": list_collections()}


@app.delete("/corpora/{corpus_id}")
def remove_corpus(corpus_id: str):
    ok = delete_collection(corpus_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Collection not found: {corpus_id}")
    return {"ok": True, "deleted": corpus_id}
