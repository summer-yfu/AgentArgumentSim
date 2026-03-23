"""Stance text rewrite via llm_do (all stance_action values)."""

from __future__ import annotations

import logging
from pathlib import Path

from connectonion import llm_do

from schemas import RevisedStanceResponse

log = logging.getLogger(__name__)
_PROMPT = (Path(__file__).parent.parent / "prompts" / "tasks" / "revise_stance.md").read_text()


def revise_stance_with_llm(
    *,
    basis_stance: str,
    stance_action: str,
    guidance: str,
    reason: str,
    ai_personality: str,
) -> str:
    """Revised stance string; raises if empty so caller can fall back."""
    user = (
        f"basis_stance:\n{basis_stance or '(empty)'}\n\n"
        f"stance_action: {stance_action}\n"
        f"guidance:\n{guidance}\n\n"
        f"reason (system):\n{reason}\n\n"
        f"ai_personality: {ai_personality or 'unspecified'}\n"
    )
    out = llm_do(
        user,
        system_prompt=_PROMPT,
        model="co/gemini-2.5-flash",
        temperature=0.3,
        output=RevisedStanceResponse,
    )
    text = (out.revised_stance or "").strip()
    if not text:
        raise ValueError("empty revised_stance from LLM")
    return text
