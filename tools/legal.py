"""Regex gate for law-mode RAG (arguer/mediator)."""

from __future__ import annotations

import re
from typing import Any

from connectonion import xray

_LEGAL_TOPIC_PATTERNS = re.compile(
    r"\b("
    r"evict|eviction|terminate|termination|notice|rent increase|rent raise|"
    r"bond|deposit|repair|repairs|entry|inspect|inspection|breach|"
    r"maintenance|cctv|camera|privacy|"
    r"law|legal|legally|rights|right|entitled|obligation|rule|regulation|"
    r"fair trading|tribunal|tenancy|lease|landlord|tenant|"
    r"allowed|prohibited|unlawful|comply|compliance"
    r")\b",
    re.IGNORECASE,
)


@xray
def detect_legal_topics(human_input: str, setup_mode: str = "general") -> dict[str, Any]:
    if (setup_mode or "").lower() != "law":
        return {"should_search": False, "query": "", "reason": "not_law_mode"}

    text = (human_input or "").strip()
    matched = _LEGAL_TOPIC_PATTERNS.findall(text)
    if not matched:
        return {"should_search": False, "query": "", "reason": "no_specific_legal_topic"}

    topic_terms = sorted({m.lower() for m in matched})
    query = f"tenancy law {' '.join(topic_terms)}"
    return {
        "should_search": True,
        "query": query,
        "reason": f"matched_topics={topic_terms}",
    }
