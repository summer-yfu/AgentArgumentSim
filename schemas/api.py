from pydantic import BaseModel, Field


class AttachRagCorpusRequest(BaseModel):
    session_id: str
    corpus_id: str


class AttachRagCorpusResponse(BaseModel):
    ok: bool = True
    rag_corpora: list[str] = Field(default_factory=list)


class TurnRequest(BaseModel):
    session_id: str
    human_input: str


class TurnResponse(BaseModel):
    reply: str
    replies: list[str] = Field(default_factory=list)
    speaker: str = "ai"
    toxicity: float = 0.0
    player_emotion: str = "neutral"
    ai_emotion: str = "neutral"
    player_goal_progress: float = 0.0
    ai_goal_progress: float = 0.0
    mediator_reply: str = ""
    stop_match: bool = False
    stop_reason: str = ""


class InitSessionRequest(BaseModel):
    session_id: str
    player_name: str = ""
    ai_name: str = ""
    relationship: str = ""
    player_role: str = ""
    ai_role: str = ""
    ai_personality: str = ""
    goal: str = ""
    player_goal: str = ""
    ai_goal: str = ""
    player_stance: str = ""
    ai_stance: str = ""
    background: str = ""
    setup_mode: str = "general"
    # Optional: indexed corpus ids (e.g. from PDF upload). Also see rag_corpus_id for single-id clients.
    rag_corpora: list[str] = Field(default_factory=list)
    rag_corpus_id: str = ""


class InitSessionResponse(BaseModel):
    ok: bool
    player_name: str = ""
    ai_name: str = ""
    relationship: str = ""
    player_role: str = ""
    ai_role: str = ""
    ai_personality: str = ""
    goal: str = ""
    player_goal: str = ""
    ai_goal: str = ""
    player_stance: str = ""
    ai_stance: str = ""
    background: str = ""
    setup_mode: str = "general"
    player_emotion: str = "neutral"
    ai_emotion: str = "neutral"
    player_goal_progress: float = 0.0
    ai_goal_progress: float = 0.0
    rag_corpora: list[str] = Field(default_factory=list)


class ParseSetupRequest(BaseModel):
    player_name: str = ""
    ai_name: str = ""
    relationship: str = ""
    background: str = ""


class ParseSetupResponse(BaseModel):
    background: str = ""
    ai_personality: str = "defensive"
    goal: str = "persuasion"
    player_goal: str = "persuasion"
    ai_goal: str = "persuasion"
    player_stance: str = ""
    ai_stance: str = ""
    relationship: str = ""
    player_role: str = ""
    ai_role: str = ""
