"""Tiny Todo Agent — Entry point."""

from __future__ import annotations

import asyncio
import sys

from agent.agent import run_cli

if __name__ == "__main__":
    resume = "--resume" in sys.argv
    asyncio.run(run_cli(resume=resume))
