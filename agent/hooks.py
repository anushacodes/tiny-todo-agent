from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import HookContext, HookMatcher, PostToolUseHookInput, PreToolUseHookInput
from claude_agent_sdk.types import SyncHookJSONOutput

LOG_FILE = Path(os.getenv("AGENT_LOG_PATH", "agent.log"))


def _log(msg: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{now}] {msg}\n")


async def pre_tool_hook(
    hook_input: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> SyncHookJSONOutput:
    name = hook_input.get("tool_name", "unknown")
    args = hook_input.get("tool_input", {})
    _log(f"[PreToolUse] Claude is calling {name} with args: {args}")
    return {}


async def post_tool_hook(
    hook_input: PostToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> SyncHookJSONOutput:
    name = hook_input.get("tool_name", "unknown")
    res = hook_input.get("tool_response")
    _log(f"[PostToolUse] Tool {name} returned: {res}")
    return {}


def get_agent_hooks() -> dict[str, list[HookMatcher]]:
    return {
        "PreToolUse": [HookMatcher(hooks=[pre_tool_hook])],
        "PostToolUse": [HookMatcher(hooks=[post_tool_hook])],
    }

