from dataclasses import dataclass, field


@dataclass
class SessionState:
    session_id: str
    player_name: str
    ai_name: str
    relationship: str
    player_role: str
    ai_role: str
    ai_personality: str
    goal: str
    player_goal: str
    ai_goal: str
    player_stance: str
    ai_stance: str
    background: str
    setup_mode: str = "general"
    history: list[dict[str, str]] = field(default_factory=list)
    player_emotion: str = "neutral"
    ai_emotion: str = "neutral"
    toxicity: float = 0.0
    player_goal_progress: float = 0.0
    ai_goal_progress: float = 0.0
    repetition_score: float = 0.0
    last_repetition_warning_round: int = -999
    stop_match: bool = False
    last_stop_reason: str = ""
    consecutive_arguer_leaks: int = 0
    rag_corpora: list[str] = field(default_factory=list)
