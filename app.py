"""Tiny Todo Agent — Entry point."""

from __future__ import annotations

import asyncio

from agent.agent import run_cli

if __name__ == "__main__":
    asyncio.run(run_cli())
