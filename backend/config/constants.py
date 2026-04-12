"""Thresholds and phrase lists for gameplay, validation, RAG."""

# Turn / round limits
MAX_ROUNDS = 30
HISTORY_TURNS = 12

# Toxicity
TOXICITY_WARNING = 0.80
TOXICITY_STOP = 0.92

# Repetition
REPETITION_ARGUER_HINT = 0.60
REPETITION_WARNING = 0.82
REPETITION_WARNING_MIN_ROUNDS = 4
REPETITION_WARNING_COOLDOWN = 2
REPETITION_STOP = 0.94
REPETITION_STOP_MIN_ROUNDS = 8

# Arguer strategy
STUBBORNNESS_HIGH = 0.70
STUBBORNNESS_VERY_HIGH = 0.85
STUBBORNNESS_LOW = 0.35
STUBBORNNESS_CONCEDE = 0.50
PLAYER_PROGRESS_THRESHOLD = 0.50
AI_LOSING_PROGRESS = 0.20
AI_LOSING_MIN_ROUND = 5
SOFTEN_MIN_ROUND = 4
NARROW_MIN_ROUND = 6
CONCEDE_MIN_ROUND = 3
LOOP_BREAK_THRESHOLD = 0.60

# Validation (reply checker)
MAX_REPLY_WORDS = 70
SIMILARITY_PREFIX_CHARS = 140
OFF_TOPIC_THRESHOLD = 0.70

# Keep in sync with Unity EmoteChanger sprites
ALLOWED_EMOTIONS = {
    "happy",
    "neutral",
    "speechless",
    "sad",
    "angry",
    "sarcastic",
    "surprised",
    "anxious",
    "awkward",
}

# Model "task done" leaks (substring match on lowercased reply; keep specific)
BANNED_AGENT_COMPLETION_MARKERS = (
    "task completed",
    "task complete",
    "task is complete",
    "task finished",
    "task done",
    "task has been completed",
    "mission accomplished",
    "assignment complete",
    "assignment completed",
    "process complete",
    "process completed",
    "objective complete",
    "objective completed",
    "request completed",
    "operation complete",
    "successfully completed the task",
    "i've completed the task",
    "i have completed the task",
    "task success",
)

# Counselor-tone phrases to flag
BANNED_SERVICE_PHRASES = [
    "i understand",
    "i get that",
    "i hear you",
    "i hear your concerns",
    "let's figure out",
    "let us figure out",
    "how about we",
    "i'm here to help",
    "i appreciate your patience",
    "thanks for being flexible",
    "reasonable compromise",
    "middle ground",
]

# Player wants to end match
PLAYER_STOP_PHRASES = (
    "game is over",
    "game over",
    "let's stop here",
    "stop here",
    "let's stop",
    "end the game",
    "end this",
    "finish game",
    "finish this",
    "finish the game",
    "i'm done",
    "we're done",
    "let's end this",
    "let's end here",
    "call it",
    "that's it",
    "i want to stop",
    "stop the game",
    "stop this",
    "i give up",
    "i quit",
    "done arguing",
    "no more",
)
PLAYER_STOP_MIN_LENGTH = 5

EMOTION_ALIASES = {
    "calm": "neutral",
    "frustrated": "anxious",
    "upset": "sad",
    "defensive": "awkward",
    "confused": "surprised",
    "embarrassed": "awkward",
    "nervous": "anxious",
    "excited": "happy",
    "disappointed": "sad",
    "irritated": "angry",
}
