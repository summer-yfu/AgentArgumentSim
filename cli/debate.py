"""Terminal frontend for the argument agent. Same backend as Unity, plus fact-checking."""

from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from simple_term_menu import TerminalMenu

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

load_dotenv(_ROOT / ".env")
load_dotenv()

# -- Colors ----------------------------------------------------------------

_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_GREY = "\033[90m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


# -- Interactive helpers ---------------------------------------------------

def _pick(prompt: str, options: list[tuple[str, str]]) -> str:
    """Arrow-key menu. Returns the value (second element) of the chosen option."""
    labels = [label for label, _ in options]
    print(f"\n{_BOLD}{prompt}{_RESET}")
    menu = TerminalMenu(
        labels,
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
    )
    idx = menu.show()
    if idx is None:
        print("Cancelled.")
        sys.exit(0)
    chosen_label, chosen_value = options[idx]
    print(f"  {_CYAN}→ {chosen_label}{_RESET}")
    return chosen_value


def _read_line(prompt: str) -> str:
    print(f"\n{_BOLD}{prompt}{_RESET}")
    return input(f"  {_CYAN}>{_RESET} ").strip()


def _read_background() -> str:
    print(f"\n{_BOLD}What's the argument about?{_RESET}")
    return input(f"  {_CYAN}>{_RESET} ").strip()




def _print_factcheck(text: str) -> None:
    """Show fact-check results in a bordered box with colored verdicts."""
    verdict_colors = {
        "supported": _GREEN,
        "contradicted": _RED,
        "mixed": _YELLOW,
        "unclear": _GREY,
    }
    stripped = (text or "").strip()
    looks_structured = bool(
        re.search(r"(?im)^\s*claim\s*:", stripped)
        or re.search(r"(?im)^\s*verdict\s*:", stripped)
    )

    def _style_line(line: str) -> str:
        raw = line.rstrip()
        low = raw.lower()
        if low.startswith("claim:"):
            return f"{_BOLD}{raw}{_RESET}"
        if low.startswith("summary:"):
            return f"{_CYAN}{_BOLD}{raw}{_RESET}"
        if low.startswith("confidence:"):
            return f"{_GREY}{raw}{_RESET}"
        vm = re.match(
            r"^(\s*verdict\s*:\s*)(supported|contradicted|mixed|unclear)(.*)$",
            raw,
            re.I,
        )
        if vm:
            w = vm.group(2).lower()
            color = verdict_colors.get(w)
            if color:
                return (
                    vm.group(1)
                    + f"{color}{vm.group(2)}{_RESET}"
                    + (vm.group(3) or "")
                )
        return raw

    print()
    print(f"  {_GREY}┌─ Fact Check ─────────────────────────────────{_RESET}")
    if not looks_structured:
        print(
            f"  {_GREY}│{_RESET} {_YELLOW}{_BOLD}!{_RESET} "
            f"{_GREY}Expected lines like{_RESET} claim: / verdict: / summary: "
            f"{_GREY}(model returned prose — check factcheck prompt or retry).{_RESET}"
        )
    for line in stripped.splitlines():
        print(f"  {_GREY}│{_RESET} {_style_line(line)}")
    print(f"  {_GREY}└────────────────────────────────────────────{_RESET}")


# -- Main flow -------------------------------------------------------------

_RELATIONSHIPS = [
    ("Friend", "friends"),
    ("Roommate", "roommates"),
    ("Sibling", "siblings"),
    ("Romantic partner", "couple"),
    ("Coworker", "coworkers"),
    ("Parent / child", "parent-child"),
    ("Rival / opponent", "opponents"),
    ("I'm the landlord (tenancy dispute)", "landlord-tenant-landlord"),
    ("I'm the tenant (tenancy dispute)", "landlord-tenant-tenant"),
]

_PERSONALITIES = [
    ("Logical", "logical"),
    ("Defensive", "defensive"),
    ("Emotional", "emotional"),
    ("Stubborn", "stubborn"),
    ("Passive-aggressive", "passive-aggressive"),
    ("Calm and diplomatic", "calm"),
]


def _resolve_relationship(raw: str) -> tuple[str, str, str, str]:
    """Returns (relationship, player_role, ai_role, setup_mode)."""
    if raw == "landlord-tenant-landlord":
        return "landlord-tenant", "landlord", "tenant", "law"
    if raw == "landlord-tenant-tenant":
        return "landlord-tenant", "tenant", "landlord", "law"
    return raw, "", "", "general"


def run_debate_cli() -> None:
    from app.orchestrator import run_turn
    from app.session import init_session
    from factcheck.checker import check_claims
    from tasks.parse_setup import parse_background

    print(f"\n{_BOLD}=== Argument Agent ==={_RESET}")
    print("Use arrow keys to pick options.\n")

    # --- Setup (same questions as Unity, just in the terminal) ---

    raw_rel = _pick("Your relationship with the opponent?", _RELATIONSHIPS)
    relationship, player_role, ai_role, setup_mode = _resolve_relationship(raw_rel)

    player_name = _read_line("What's your name?") or "Player"
    ai_name = _read_line("Name for the AI opponent?") or "Opponent"

    background = _read_background()
    if not background:
        print(f"  {_GREY}(no background — using a placeholder){_RESET}")
        background = "A disagreement between two parties; details were not specified."

    ai_personality = _pick("AI personality?", _PERSONALITIES)
    player_goal = "persuasion"
    ai_goal = "persuasion"

    # --- Parse background (LLM extracts stances, cleans up roles) ---

    print(f"\n{_GREY}Setting up…{_RESET}")
    parsed = parse_background(
        player_name=player_name,
        ai_name=ai_name,
        relationship=relationship,
        background=background,
    )

    player_stance = parsed.player_stance or ""
    ai_stance = parsed.ai_stance or ""
    merged_bg = parsed.background or background
    pr = parsed.player_role or player_role
    ar = parsed.ai_role or ai_role
    rel = parsed.relationship or relationship

    # --- Summary ---

    summary = (
        f"  {_BOLD}Relationship:{_RESET} {rel}\n"
        f"  {_BOLD}You:{_RESET} {player_name}  {_GREY}|{_RESET}  {_BOLD}AI:{_RESET} {ai_name}\n"
        + (f"  {_BOLD}Roles:{_RESET} {pr} vs {ar}\n" if pr and ar else "")
        + f"  {_BOLD}AI personality:{_RESET} {ai_personality}\n"
        f"\n  {_BOLD}Background:{_RESET}\n  {merged_bg}\n"
        f"\n  {_BOLD}Your stance:{_RESET} {player_stance}\n"
        f"  {_BOLD}AI stance:{_RESET} {ai_stance}"
    )

    print(f"\n{_GREY}{'─' * 50}{_RESET}")
    print(summary)
    print(f"{_GREY}{'─' * 50}{_RESET}")
    print(f"\n{_GREY}[Enter] start  |  q abort{_RESET}")
    if input().strip().lower() in ("q", "quit", "exit"):
        print("Aborted.")
        return

    # --- Create session (identical to what Unity POST /init_session does) ---

    session_id = str(uuid.uuid4())
    init_session(
        session_id=session_id,
        player_name=player_name,
        ai_name=ai_name,
        relationship=rel,
        player_role=pr,
        ai_role=ar,
        ai_personality=ai_personality,
        goal=ai_goal,
        player_goal=player_goal,
        ai_goal=ai_goal,
        player_stance=player_stance,
        ai_stance=ai_stance,
        background=merged_bg,
        setup_mode=setup_mode,
        rag_corpora=[],
    )

    # --- Debate loop ---

    print(f"\n{_GREEN}{'═' * 50}{_RESET}")
    print(f"{_BOLD}Let's go.{_RESET}")
    print(f"Type your argument and press Enter. The AI will respond.")
    print(f"{_GREY}Commands: /quit  /fc off  /fc on  /summary{_RESET}")
    print(f"{_GREEN}{'═' * 50}{_RESET}")
    print(f"\n{_GREY}Your turn — make your opening argument:{_RESET}")
    factcheck_on = True

    while True:
        try:
            human = input(f"\n{_BOLD}[{player_name}]{_RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not human:
            continue
        if human.lower() in ("/quit", "/q", ":q"):
            print("Bye.")
            break
        if human.lower() == "/summary":
            print(summary)
            continue
        if human.lower() in ("/fc on", "/factcheck on"):
            factcheck_on = True
            print(f"  {_GREEN}Fact-check ON{_RESET}")
            continue
        if human.lower() in ("/fc off", "/factcheck off"):
            factcheck_on = False
            print(f"  {_GREY}Fact-check OFF{_RESET}")
            continue

        # --- Run one turn through the orchestrator ---

        try:
            out = run_turn(session_id, human)
        except Exception as exc:
            print(f"\n{_RED}[error]{_RESET} {exc}")
            continue

        # --- Show AI reply ---

        replies = out.get("replies") or []
        if not replies and out.get("reply"):
            replies = [out["reply"]]
        for i, bubble in enumerate(replies):
            label = ai_name if i == 0 else f"{ai_name} (cont.)"
            print(f"\n{_CYAN}{_BOLD}[{label}]{_RESET}\n{bubble}")

        # --- Fact-check the AI's reply ---

        if factcheck_on and replies:
            print(f"\n{_GREY}Connecting to fact checker now. Please wait.{_RESET}")
            try:
                fc_text = check_claims(" ".join(replies))
                if fc_text:
                    _print_factcheck(fc_text)
                else:
                    print(f"\n  {_GREY}(fact-checker unavailable — is factcheck.server running?){_RESET}")
            except Exception as exc:
                print(f"\n  {_GREY}(fact-check error: {exc}){_RESET}")

        # --- Show mediator if it intervened ---

        med = (out.get("mediator_reply") or "").strip()
        if med:
            print(f"\n{_YELLOW}{_BOLD}[Mediator]{_RESET}\n{med}")

        # --- Check if match ended ---

        if out.get("stop_match"):
            reason = out.get("stop_reason") or "unknown"
            print(f"\n{_RED}--- Match ended ({reason}) ---{_RESET}")
            break

        print(f"\n{_GREY}Your turn:{_RESET}")


if __name__ == "__main__":
    run_debate_cli()
