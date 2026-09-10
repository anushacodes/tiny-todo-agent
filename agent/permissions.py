from __future__ import annotations

import asyncio
from typing import Any

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext


async def check_tool_permission(
    tool_name: str, tool_input: dict[str, Any], context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    if "list_todos" in tool_name:
        return PermissionResultAllow()

    name = tool_name.split("__")[-1]
    try:
        ans = await asyncio.to_thread(input, f"\nAllow {name}{tool_input}? [y/N]: ")
    except (EOFError, KeyboardInterrupt):
        return PermissionResultDeny(message="Cancelled.")

    if ans.strip().lower() in ("y", "yes"):
        return PermissionResultAllow()
    return PermissionResultDeny(message=f"Denied {name}.")
