from __future__ import annotations

import asyncio
from typing import Any

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext


from agent.ui import console, print_permission_prompt


_batch_approved: bool = False


def reset_turn_permissions() -> None:
    global _batch_approved
    _batch_approved = False


async def check_tool_permission(
    tool_name: str, tool_input: dict[str, Any], context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    global _batch_approved

    # Auto-allow non-destructive operations: listing, adding, and completing tasks
    if any(safe in tool_name for safe in ("list_todos", "add_todo", "complete_todo")):
        return PermissionResultAllow()

    name = tool_name.split("__")[-1]

    if _batch_approved:
        console.print(f"[bold green]✅ Auto-approved {name} (batch approval active)[/bold green]\n")
        return PermissionResultAllow()

    print_permission_prompt(tool_name, tool_input)
    try:
        ans = await asyncio.to_thread(
            console.input, "[bold red]❓ Allow this action? [y/N/all]: [/bold red]"
        )
    except (EOFError, KeyboardInterrupt):
        return PermissionResultDeny(message="Cancelled.")

    cleaned = ans.strip().lower()

    if cleaned in ("all", "a", "yes all", "y all"):
        _batch_approved = True
        console.print(f"[bold green]✅ Approved {name} and remaining actions in batch![/bold green]\n")
        return PermissionResultAllow()

    if cleaned.startswith("y") or cleaned in ("ok", "okay", "sure", "s", "1", "true"):
        console.print("[bold green]✅ Approved![/bold green]\n")
        return PermissionResultAllow()

    console.print(f"[bold red]❌ Denied {name}.[/bold red]\n")
    return PermissionResultDeny(message=f"User declined permission to {name}. Do not retry this action.")
