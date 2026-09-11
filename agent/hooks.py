from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import HookContext, HookMatcher
from claude_agent_sdk.types import SyncHookJSONOutput

LOG_FILE = Path(os.getenv("AGENT_LOG_PATH", "agent.log"))


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


from agent.ui import print_tool_call, print_tool_result


async def pre_tool_hook(hook_input, tool_use_id: str | None, context: HookContext) -> SyncHookJSONOutput:
    tool_name = hook_input.get("tool_name", "")
    tool_input_data = hook_input.get("tool_input", {})
    _log(f"[PreToolUse] {tool_name} {tool_input_data}")
    print_tool_call(tool_name, tool_input_data)
    return {}


async def post_tool_hook(hook_input, tool_use_id: str | None, context: HookContext) -> SyncHookJSONOutput:
    tool_name = hook_input.get("tool_name", "")
    tool_response = hook_input.get("tool_response")
    _log(f"[PostToolUse] {tool_name} -> {tool_response}")
    print_tool_result(tool_name, tool_response)
    return {}


def get_agent_hooks() -> dict[str, list[HookMatcher]]:
    return {
        "PreToolUse": [HookMatcher(hooks=[pre_tool_hook])],
        "PostToolUse": [HookMatcher(hooks=[post_tool_hook])],
    }
