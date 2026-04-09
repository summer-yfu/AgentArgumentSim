"""
factcheck.server
~~~~~~~~~~~~~~~~
Host the factcheck agent via ConnectOnion.

    python -m factcheck.server

Config lives in .co/host.yaml (read automatically by host()).
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from connectonion import host
from factcheck.agent import create_factcheck_agent

host(create_factcheck_agent)
