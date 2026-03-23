# Initial Emotions

Infer the likely initial emotions of each party BEFORE any conversation has occurred, based on the setup background.

## Allowed Emotions

Use ONLY one of these exact strings: `happy`, `neutral`, `speechless`, `sad`, `angry`, `sarcastic`, `surprised`, `anxious`, `awkward`

Do NOT output any other emotion word. If genuinely unsure, use `neutral`.

## Decision Guide

| Situation | Player likely feels | AI likely feels |
|---|---|---|
| Heated conflict (accusations, broken trust) | `angry` or `sad` | `defensive` personality → `anxious`; `stubborn` → `angry` |
| Money dispute (unpaid debt, withheld bond) | `angry` or `anxious` | `passive-aggressive` → `awkward`; `defensive` → `anxious` |
| Embarrassing or awkward situation | `awkward` | `awkward` or `anxious` |
| Something unexpected just happened | `surprised` | `surprised` or `anxious` |
| Calm, neutral setup with mild disagreement | `neutral` | `neutral` |
| Long-simmering resentment, passive tension | `sad` or `anxious` | `sad` or `anxious` |

## Examples

### Example 1: Aggressive conflict

Background: "My roommate has been playing loud music at 2 AM every night and refuses to stop. I've asked three times."
AI personality: stubborn

**Bad**: player_emotion = `neutral`, ai_emotion = `neutral` (ignores the clear tension)
**Good**: player_emotion = `angry`, ai_emotion = `angry`

### Example 2: Awkward situation

Background: "I walked in on my roommate wearing my clothes. They didn't know I'd be home early."
AI personality: passive-aggressive

**Bad**: player_emotion = `angry` (over-reads the tension — it's more weird than hostile)
**Good**: player_emotion = `surprised`, ai_emotion = `awkward`

### Example 3: Financial tension

Background: "My landlord hasn't returned my bond after 3 months. He keeps saying 'soon' but nothing happens."
AI personality: defensive

**Bad**: player_emotion = `sad` (this is frustration, not sadness)
**Good**: player_emotion = `anxious`, ai_emotion = `anxious`

## Critical Rule

When the background describes real tension, do NOT default to `neutral`. Match the emotion to the situation.

## Output

Return `player_emotion` and `ai_emotion`, each one of the 9 allowed strings above.
