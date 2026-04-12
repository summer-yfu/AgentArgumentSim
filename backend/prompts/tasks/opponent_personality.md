# Opponent Personality Analyzer

Analyze how the **human** (opponent) is communicating so the AI opponent can adapt its strategy.

## Input

- `recent_history` — recent conversation lines (may include speaker labels like Human:, AI:, Mediator:).
- `latest_human_message` — the human's current message if not fully captured in history.

## Output Fields

| Field | Type | Description |
|---|---|---|
| `opponent_traits` | list of strings | Communication traits observed in the human's messages (use trait vocabulary below) |
| `opponent_avg_message_length` | float | Average word count per human message (rough estimate) |
| `strategy_notes` | list of strings | 2–5 short, actionable bullets advising the AI how to respond |

## Trait Vocabulary

Use a subset. Include `neutral` only if nothing else fits.

| Trait | What it looks like in their messages |
|---|---|
| `aggressive` | Insults, threats, hostility, personal attacks, escalation ("You're such a liar", "This is BS") |
| `analytical` | Structured arguments, cites evidence, asks for reasoning ("Section 3.2 says...", "Can you prove that?") |
| `emotional` | Feeling-forward, personal stories, appeals to empathy ("You have no idea how that made me feel") |
| `verbose` | Long messages, over-explains, walls of text |
| `terse` | One-liners, minimal engagement ("Fine.", "Whatever.", "k") |
| `evasive` | Dodges questions, changes subject, avoids direct answers ("That's not the point", "Let's talk about something else") |
| `manipulative` | Guilt-tripping, strawmanning, false equivalences, gaslighting ("So you're saying you don't care about me at all?") |
| `neutral` | Calm, no strong signal in any direction |

## Examples

### Example 1: Disengaged / passive-aggressive

Human messages: "Whatever. You always do this." / "Fine, I guess it doesn't matter."

**Output**:
- Traits: `terse`, `manipulative`
- Avg words: 6.0
- Strategy notes:
  - Opponent is disengaging — don't mirror the passive tone
  - Ask a direct question to re-engage them
  - Keep responses short; match their brevity
  - Don't take the bait on "you always" generalizations

### Example 2: Evidence-focused

Human messages: "That's not what the lease says. Section 3.2 explicitly states..." / "Can you point to where it says that?"

**Output**:
- Traits: `analytical`
- Avg words: 12.0
- Strategy notes:
  - Opponent is evidence-focused — unsupported claims will lose credibility
  - Stay structured and cite specific points
  - Don't get emotional; match their precision
  - If you don't have evidence, acknowledge the gap honestly

### Example 3: Emotionally escalated

Human messages: "I can't believe you would do this to me. After everything I've done for you." / "You literally don't care about anyone but yourself."

**Output**:
- Traits: `emotional`, `aggressive`
- Avg words: 14.0
- Strategy notes:
  - Opponent is emotionally charged — avoid dismissive responses
  - Acknowledge the feeling briefly, then redirect to the issue
  - Don't escalate; stay firm but not cold
  - Use concrete facts to ground the exchange

## Rules

- Base traits on evidence in the text; if unclear, prefer fewer traits plus `neutral`.
- Do not invent facts about the human beyond what the text shows.
- `strategy_notes` must be in English, imperative form. Do not mention "the model" or "JSON".
