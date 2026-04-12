"""
factcheck.checker
~~~~~~~~~~~~~~~~~
Client used by cli/debate.py to talk to the hosted factcheck agent.

Uses ConnectOnion connect() which handles Ed25519 signing automatically.
The factcheck server must be running: python -m factcheck.server
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)


# "have to strictly follow this output format"
# is there a way to not use prompt
# Repeated at send-time so the model cannot bury the template under tool results.
_OUTPUT_FORMAT_REMINDER = """

---
FINAL MESSAGE RULES (required):
- Your *entire* last reply must be ONLY the structured template from your system prompt (claim / verdict / confidence / reason / evidence / summary).
- Do not write an introduction or prose summary (e.g. "The statement is accurate…") before or instead of those lines. The CLI searches for lines like `claim:` and `verdict:`.
- Do not wrap the output in markdown code fences.
"""

_proxy = None

from connectonion import connect, address
from pathlib import Path



# Connect with the factcheck agent
def check_claims(text: str) -> str | None:
    """Send debate text to the factcheck agent, return its verdict.

    Returns None if the agent is unreachable or the input is empty.
    """
    if not (text or "").strip():
        return None

    factcheck_addr = os.environ.get("FACTCHECK_ADDRESS", "").strip()
    if not factcheck_addr:
        log.warning("FACTCHECK_ADDRESS not set — skipping fact-check")
        return None

    try:
        global _proxy
        if _proxy is None:
            log.info("Connecting to factcheck agent...")
            keys = address.load(Path(".co"))
            _proxy = connect(factcheck_addr, keys=keys)

        response = _proxy.input(
            f"Here's what was just said in a debate. Check the facts:\n\n{text}"
            f"{_OUTPUT_FORMAT_REMINDER}"
        )
        return response.text
    except Exception as exc:
        log.warning("Factcheck failed: %s", exc)
        _proxy = None
        return None
