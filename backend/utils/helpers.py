"""Small shared helpers (clamp, history text, emotion map)."""

from config.constants import ALLOWED_EMOTIONS, EMOTION_ALIASES, HISTORY_TURNS
from schemas import SessionState


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def normalize_emotion(s: str) -> str:
    if not s or not isinstance(s, str):
        return "neutral"
    norm = s.strip().lower()
    if norm in ALLOWED_EMOTIONS:
        return norm
    return EMOTION_ALIASES.get(norm, "neutral")


def stubbornness_for_personality(personality: str) -> float:
    mapping = {
        "calm": 0.25,
        "logical": 0.45,
        "defensive": 0.65,
        "emotional": 0.7,
        "passive-aggressive": 0.75,
        "stubborn": 0.9,
    }
    return mapping.get((personality or "").strip().lower(), 0.55)


def recent_history_text(
    state: SessionState,
    turns: int = HISTORY_TURNS,
    use_display_names: bool = False,
) -> str:
    recent = state.history[-turns:]
    if not recent:
        return "(no previous turns)"
    if use_display_names:
        name_map = {
            "human": getattr(state, "player_name", None) or "human",
            "ai": getattr(state, "ai_name", None) or "AI",
            "mediator": "Mediator",
        }
        return "\n".join(
            f"{name_map.get(item['speaker'], item['speaker'])}: {item['text']}"
            for item in recent
        )
    return "\n".join(f"{item['speaker']}: {item['text']}" for item in recent)
