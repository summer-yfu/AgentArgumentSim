"""
Creating Fact-check agent, assembled for ConnectOnion host().

Playwright + Chromium are required for BrowserAutomation (see requirements.txt).
Set FACTCHECK_DISABLE_BROWSER=1 to run WebFetch-only (e.g. CI).
https://docs.connectonion.com/useful-tools/browser-tools
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from connectonion import Agent, WebFetch
from connectonion.useful_tools.browser_tools import BrowserAutomation
from ddgs import DDGS

from rag import list_collections, search_documents

log = logging.getLogger(__name__)

_browser_singleton = None


def _browser_disabled() -> bool:
    return os.environ.get("FACTCHECK_DISABLE_BROWSER", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _browser_tool_instances() -> list:
    """[] if disabled; else one process-wide BrowserAutomation."""
    global _browser_singleton
    if _browser_disabled():
        return []
    if _browser_singleton is None:
        headless = os.environ.get("FACTCHECK_BROWSER_HEADLESS", "1").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        chrome_profile = os.environ.get(
            "FACTCHECK_BROWSER_USE_CHROME_PROFILE",
            "",
        ).strip().lower() in ("1", "true", "yes")
        _browser_singleton = BrowserAutomation(
            use_chrome_profile=chrome_profile,
            headless=headless,
        )
    return [_browser_singleton]


TRUSTED_DOMAINS = {
    "wikipedia.org", "gov.au", "gov", "who.int",
    "ourworldindata.org", "abs.gov.au", "fairwork.gov.au",
    "legislation.gov.au", "bbc.com", "reuters.com", "apnews.com",
}


def _is_trusted(url: str) -> bool:
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in TRUSTED_DOMAINS)


def search_corpus(
    query: str,
    corpus_ids: list[str] | None = None,
    top_k: int = 5,
) -> str:
    """Search the local document index (law, tenancy, policy PDFs).
    Best first step for any legal or regulatory claim."""
    return search_documents(query=query, corpus_ids=corpus_ids, top_k=top_k)


def list_rag_collections() -> str:
    """List available document collections so you know what to search."""
    try:
        names = list_collections()
    except Exception as exc:
        log.warning("list_collections failed: %s", exc)
        return f"[error: {exc}]"
    if not names:
        return "(no collections indexed)"
    return "Collections:\n" + "\n".join(f"  - {n}" for n in names)


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for a factual claim. Returns titles, snippets, and URLs
    from trusted sources. Use this to find real URLs before fetching pages."""
    try:
        results = DDGS().text(query, max_results=max_results * 2)
    except Exception as exc:
        log.warning("DuckDuckGo search failed: %s", exc)
        return f"[search failed: {exc}]"

    if not results:
        return "(no results found)"

    trusted = [r for r in results if _is_trusted(r.get("href", ""))]
    picked = trusted[:max_results] if trusted else results[:max_results]

    lines = []
    for r in picked:
        tag = "" if _is_trusted(r.get("href", "")) else " [unverified source]"
        lines.append(f"- {r.get('title', '?')}\n  {r.get('href', '')}{tag}\n  {r.get('body', '')}")
    return "\n".join(lines)


def create_factcheck_agent() -> Agent:
    """Called by server.py → host()."""
    prompt_file = Path(__file__).resolve().parent / "prompts" / "factcheck.md"
    system_prompt = prompt_file.read_text(encoding="utf-8")

    browser_tools = _browser_tool_instances()

    webfetchtool = WebFetch()
    tools = [
        search_corpus,
        list_rag_collections,
        web_search,
        webfetchtool,
    ] + list(browser_tools)

    max_iterations = 20 if browser_tools else 12

    return Agent(
        name="factcheck",
        system_prompt=system_prompt,
        tools=tools,
        model="co/gemini-2.5-pro",
        max_iterations=max_iterations,
    )
