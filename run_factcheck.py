"""Factcheck server entry point — run from repo root: python run_factcheck.py"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from factcheck.server import *  # noqa: F401,F403 — triggers host()
