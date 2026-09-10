from __future__ import annotations

import asyncio
import os

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage, TextBlock
from dotenv import load_dotenv

from agent.hooks import get_agent_hooks
from agent.permissions import check_tool_permission
from agent.subagents import get_agent_definitions

load_dotenv()

DEFAULT_MODEL = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")


def _get_sdk_env() -> dict[str, str]:
    env: dict[str, str] = {}
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if openrouter_key or "openrouter.ai" in base_url:
        env["ANTHROPIC_BASE_URL"] = base_url or "https://openrouter.ai/api"
        env["ANTHROPIC_AUTH_TOKEN"] = openrouter_key
        env["ANTHROPIC_API_KEY"] = ""
    elif anthropic_key:
        env["ANTHROPIC_API_KEY"] = anthropic_key
        if base_url:
            env["ANTHROPIC_BASE_URL"] = base_url
    return env


def build_agent_options(can_use_tool=check_tool_permission) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=(
            "You are a friendly todo assistant. Help the user inspect, modify, and reason "
            "about tasks using the todo tools. Always use the right tool for add/list/complete/delete. "
            "Delegate prioritization questions to the 'prioritizer' subagent. Keep responses concise."
        ),
        mcp_servers={"todo-server": {"type": "stdio", "command": "uv", "args": ["run", "python", "mcp_server.py"]}},
        can_use_tool=can_use_tool,
        permission_mode="default",
        hooks=get_agent_hooks(),
        agents=get_agent_definitions(),
        setting_sources=["project"],
        env=_get_sdk_env(),
    )


async def run_cli() -> None:
    print("=" * 60)
    print("Tiny Todo Agent (Claude Agent SDK)")
    print("Try: 'Add learn Redis', 'List my todos'")
    print("Type 'exit' or 'quit' to close.")
    print("=" * 60)

    options = build_agent_options()

    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                try:
                    user_input = await asyncio.to_thread(input, "\n> ")
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                prompt = user_input.strip()
                if not prompt:
                    continue
                if prompt.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break

                try:
                    await client.query(prompt)
                    async for message in client.receive_response():
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    print(f"\n{block.text}")
                        elif isinstance(message, ResultMessage) and message.is_error and message.result:
                            print(f"\n[Agent Error]: {message.result}")
                except Exception as exc:
                    print(f"\n[Error]: {exc}")
    except Exception as exc:
        print(f"\nFailed to initialize: {exc}")
