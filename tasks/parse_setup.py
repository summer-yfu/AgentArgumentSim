"""Background text -> structured setup (llm_do)."""

import logging
from pathlib import Path

from connectonion import llm_do

from schemas import ParseSetupResponse

log = logging.getLogger(__name__)
SETUP_PARSER_PROMPT = (
    Path(__file__).parent.parent / "prompts" / "tasks" / "setup_parser.md"
).read_text()


def parse_background(player_name: str, ai_name: str, relationship: str, background: str) -> ParseSetupResponse:
    fallback = ParseSetupResponse(
        background=background or "No background provided.",
        ai_personality="defensive",
        goal="persuasion",
        player_goal="persuasion",
        ai_goal="persuasion",
        player_stance="The current behavior or situation is not acceptable.",
        ai_stance="The current behavior or situation is acceptable or justified.",
        relationship=relationship or "unknown",
    )

    if not (background or "").strip():
        return fallback

    try:
        out = llm_do(
            f"player_name: {player_name}\nai_name: {ai_name}\nrelationship: {relationship}\nbackground: {background}",
            system_prompt=SETUP_PARSER_PROMPT,
            model="co/gemini-2.5-flash",
            output=ParseSetupResponse,
        )
        return ParseSetupResponse(
            background=out.background or background,
            ai_personality=out.ai_personality or "defensive",
            goal=out.ai_goal or out.goal or "persuasion",
            player_goal=out.player_goal or out.goal or "persuasion",
            ai_goal=out.ai_goal or out.goal or "persuasion",
            player_stance=out.player_stance or fallback.player_stance,
            ai_stance=out.ai_stance or fallback.ai_stance,
            relationship=out.relationship or relationship or "unknown",
            player_role=out.player_role or "",
            ai_role=out.ai_role or "",
        )
    except Exception as e:
        log.warning("parse_background failed: %s", e, exc_info=True)
        return fallback
