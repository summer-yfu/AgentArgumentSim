"""Terminal entry: python -m cli  (same as python -m cli debate)."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m cli",
        description="Argument Agent — run a debate in the terminal (no Unity).",
    )
    parser.set_defaults(func=_run_debate)

    sub = parser.add_subparsers(dest="command", required=False)
    debate_p = sub.add_parser(
        "debate",
        help="Same as running with no arguments (kept for scripts / muscle memory).",
    )
    debate_p.set_defaults(func=_run_debate)

    args = parser.parse_args()
    args.func()


def _run_debate() -> None:
    from cli.debate import run_debate_cli

    run_debate_cli()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        sys.exit(130)
