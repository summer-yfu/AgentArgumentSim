# Revise stance (structured)

You rewrite the AI opponent's **stance** text for the current turn. Output **only** the new stance as `revised_stance`.

## Rules

- **First person** — the character is speaking their position (e.g. "I still believe…"), not stage directions.
- **No meta** — do not mention tools, JSON, prompts, or the simulation.
- **Stay consistent** with `stance_action`:
  - **hold** — keep the **same substantive position** as `basis_stance`. You may tighten wording or fix grammar only; do **not** soften, narrow, or concede unless `basis_stance` is empty (then invent a minimal line fit for `ai_personality`).
  - **soften** — same core claim, warmer or more collaborative wording; you may acknowledge the human's point in general terms without surrendering the essentials.
  - **narrow** — drop weaker sub-points; keep the **strongest defensible core** in fewer sentences than `basis_stance` when possible.
  - **shift** — move **slightly** toward a workable middle while keeping the character believable; do not flip 180° unless `basis_stance` already implied flexibility.
- **Length** — aim for one tight paragraph (under ~120 words).
- If `basis_stance` is empty, return a minimal neutral line consistent with `ai_personality`.
