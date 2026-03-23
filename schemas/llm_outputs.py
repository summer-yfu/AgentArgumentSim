from pydantic import BaseModel, Field


class InitialEmotions(BaseModel):
    player_emotion: str = "neutral"
    ai_emotion: str = "neutral"


class ConversationAnalysis(BaseModel):
    player_emotion: str = "neutral"
    ai_emotion: str = "neutral"
    toxicity: float = 0.15
    repetition_score: float = 0.0
    goal_reached: bool = False
    off_topic_score: float = 0.0
    player_goal_progress: float = 0.0
    ai_goal_progress: float = 0.0


class RevisedStanceResponse(BaseModel):
    revised_stance: str = Field(
        ...,
        description="First-person stance text for this turn",
    )


class OpponentPersonalityAnalysis(BaseModel):
    opponent_traits: list[str] = Field(
        default_factory=lambda: ["neutral"],
        description="Style tags, e.g. aggressive, analytical, terse",
    )
    opponent_avg_message_length: float = Field(
        default=10.0,
        ge=0.0,
        description="Approximate words per recent human message",
    )
    strategy_notes: list[str] = Field(
        default_factory=list,
        description="Short hints for the arguer",
    )
