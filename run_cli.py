"""CLI entry point — run from repo root: python run_cli.py"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from cli.debate import run_debate_cli

if __name__ == "__main__":
    try:
        run_debate_cli()
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted.\n")
        sys.exit(130)
