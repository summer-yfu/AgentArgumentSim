# Setup Parser

Extract structured fields from the user's freeform background description to initialize an argument simulation.

## Input

- **player_name**: The human player's name.
- **ai_name**: The AI opponent's name.
- **relationship**: The relationship between human and AI (e.g. friends, roommates, landlord-tenant).
- **background**: The user's freeform description of the conflict.

## Critical Rule — Stance Assignment

Use **player_name** and **ai_name** to correctly assign stances and roles.

- If the background mentions the AI's name taking a position → that is **ai_stance**
- If the background mentions the player's name taking a position → that is **player_stance**
- Do NOT swap them. This is the most common error.

**Bad** (swapped):
Background: "Jordan (player) wants to keep the dog. Alex (AI) says no pets allowed."
→ ai_stance: "Wants to keep the dog" / player_stance: "No pets allowed"

**Good** (correct):
→ player_stance: "Wants to keep the dog in the apartment."
→ ai_stance: "No pets allowed in the shared space."

## Output Fields

| Field | Type | How to infer it |
|---|---|---|
| `background` | string | Keep or lightly summarize the original text |
| `ai_personality` | enum | Infer from the conflict tone and the AI character's behavior (see options below) |
| `goal` | enum | Same value as `ai_goal` (legacy field) |
| `player_goal` | enum | What the human is trying to achieve in this dispute |
| `ai_goal` | enum | What the AI is trying to achieve in this dispute |
| `relationship` | string | The relationship between the two sides |
| `player_role` | string | "landlord" or "tenant" for tenancy disputes; empty string otherwise |
| `ai_role` | string | The opposing role; empty string if not applicable |
| `player_stance` | string | One short sentence — the human's position on the core dispute |
| `ai_stance` | string | One short sentence — the AI's position on the core dispute |

### Personality options
`defensive`, `logical`, `emotional`, `stubborn`, `passive-aggressive`, `calm`

### Goal options
`persuasion`, `conflict_resolution`, `truth_seeking`, `decision`, `verbal_fight`

Infer goals separately for each side. If the human wants to resolve things peacefully but the AI character is described as combative, they may have different goals.

## Examples

### Example 1: Roommate conflict

**Input**: player_name="Sam", ai_name="Riley", relationship="roommates"
Background: "Riley keeps eating on my bed and leaving crumbs everywhere. I've told them to stop but they say it's not a big deal. I'm getting really frustrated."

**Output**:
- background: "Riley keeps eating on Sam's bed and leaving crumbs. Sam has asked them to stop but Riley dismisses it."
- ai_personality: `stubborn`
- player_goal: `decision` (Sam wants a concrete rule: stop eating on the bed)
- ai_goal: `persuasion` (Riley wants Sam to accept it's fine)
- player_stance: "Eating on the bed is not acceptable and needs to stop."
- ai_stance: "Eating on the bed is fine and not a big deal."
- player_role: ""
- ai_role: ""

### Example 2: Landlord-tenant dispute

**Input**: player_name="Chen", ai_name="Mr. Park", relationship="landlord-tenant"
Background: "My landlord Mr. Park hasn't returned my bond even though I cleaned the apartment. He claims there's damage but won't show me any evidence."

**Output**:
- background: "Chen's landlord Mr. Park is withholding the bond, claiming damage without providing evidence. Chen cleaned the apartment."
- ai_personality: `defensive`
- player_goal: `decision` (Chen wants the bond returned)
- ai_goal: `persuasion` (Mr. Park wants to justify keeping it)
- player_stance: "The bond should be returned because the apartment was cleaned and no damage evidence was provided."
- ai_stance: "The bond is being withheld due to property damage."
- player_role: "tenant"
- ai_role: "landlord"

### Example 3: Friends disagreement

**Input**: player_name="Mia", ai_name="Jake", relationship="close friends"
Background: "Jake borrowed $200 from me three months ago and keeps avoiding paying it back. He says he'll get to it but never does."

**Output**:
- background: "Jake borrowed $200 from Mia three months ago and has been avoiding repayment despite repeated promises."
- ai_personality: `passive-aggressive`
- player_goal: `decision` (Mia wants a concrete repayment commitment)
- ai_goal: `conflict_resolution` (Jake wants to smooth things over without committing)
- player_stance: "The $200 loan needs to be repaid now."
- ai_stance: "I'll get to it when I can, stop pressuring me."
- player_role: ""
- ai_role: ""
