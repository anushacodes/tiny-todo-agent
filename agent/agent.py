from __future__ import annotations

import asyncio
import os

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
)
from dotenv import load_dotenv

from pathlib import Path

from agent.hooks import _log, get_agent_hooks
from agent.permissions import check_tool_permission, reset_turn_permissions
from agent.proxy import get_openrouter_proxy_port, get_proxy_port
from agent.subagents import get_agent_definitions
from agent.ui import (
    console,
    print_assistant_message,
    print_banner,
    print_error,
    print_farewell,
    print_help,
    print_thinking,
    print_user_prompt,
)

load_dotenv()


def _get_model_name() -> str:
    explicit = os.getenv("MODEL_NAME")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if anthropic_key and (not explicit or explicit in ("openrouter/free", "llama-3.3-70b-versatile")):
        return "claude-3-5-sonnet-20241022"
    if groq_key and (not explicit or explicit == "openrouter/free"):
        return "llama-3.3-70b-versatile"
    if explicit:
        return explicit
    return "openrouter/free"


SESSION_FILE = Path(os.getenv("SESSION_FILE_PATH", ".session_id"))


def _save_session_id(sid: str) -> None:
    SESSION_FILE.write_text(sid.strip(), encoding="utf-8")


def _load_session_id() -> str | None:
    return SESSION_FILE.read_text(encoding="utf-8").strip() if SESSION_FILE.exists() else None


def _get_sdk_env() -> dict[str, str]:
    env: dict[str, str] = {}
    groq_key = os.getenv("GROQ_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "")

    if anthropic_key:
        env["ANTHROPIC_API_KEY"] = anthropic_key
        if base_url:
            env["ANTHROPIC_BASE_URL"] = base_url
    elif groq_key:
        target_model = _get_model_name()
        proxy_port = get_proxy_port(provider="groq", groq_key=groq_key, model=target_model)
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{proxy_port}"
        env["ANTHROPIC_AUTH_TOKEN"] = "dummy"
        env["ANTHROPIC_API_KEY"] = ""
    elif openrouter_key:
        target_model = _get_model_name()
        proxy_port = get_proxy_port(provider="openrouter", openrouter_key=openrouter_key, model=target_model)
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{proxy_port}"
        env["ANTHROPIC_AUTH_TOKEN"] = "dummy"
        env["ANTHROPIC_API_KEY"] = ""
    elif base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    return env


PLUGIN_DIR = Path(os.getenv("PLUGIN_DIR", "todo-plugin")).resolve()


def _filter_stderr(line: str) -> None:
    if "unrecognized_model" in line or "query_source" in line:
        return
    if line.strip():
        _log(f"[stderr] {line.strip()}")


def build_agent_options(can_use_tool=check_tool_permission, resume_session_id: str | None = None) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        model=_get_model_name(),
        system_prompt=(
            "You are a friendly, fast todo assistant. Execute user actions directly and cleanly. "
            "Do NOT produce verbose reasoning or deliberation for simple actions (add, list, complete, delete). "
            "When asked to delete all tasks, invoke delete_todo for each ID. "
            "If the user declines permission for an action, accept their choice immediately without retrying or debating it. "
            "Delegate prioritization questions to the 'prioritizer' subagent. Keep responses brief and helpful."
        ),
        mcp_servers={"todo-server": {"type": "stdio", "command": "uv", "args": ["run", "python", "mcp_server.py"]}},
        can_use_tool=can_use_tool,
        permission_mode="default",
        hooks=get_agent_hooks(),
        agents=get_agent_definitions(),
        setting_sources=["project"],
        plugins=[{"type": "local", "path": str(PLUGIN_DIR)}] if PLUGIN_DIR.exists() else [],
        resume=resume_session_id,
        stderr=_filter_stderr,
        env=_get_sdk_env(),
    )


EXIT_COMMANDS = {
    "exit",
    "quit",
    "bye",
    "goodbye",
    "bye bye",
    "cya",
    "see ya",
    "/end",
    "/exit",
    "/quit",
    "/bye",
    "/stop",
    "q",
    ":q",
}

HELP_COMMANDS = {
    "help",
    "/help",
    "?",
    ":help",
    "-h",
    "--help",
}


def _is_exit_command(text: str) -> bool:
    cleaned = text.strip().lower().rstrip("!.,")
    return cleaned in EXIT_COMMANDS


def _is_help_command(text: str) -> bool:
    cleaned = text.strip().lower()
    return cleaned in HELP_COMMANDS


async def run_cli(resume: bool = False) -> None:
    resume_sid = _load_session_id() if resume else None
    print_banner(resume_session_id=resume_sid)

    options = build_agent_options(resume_session_id=resume_sid)

    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                try:
                    user_input = await asyncio.to_thread(print_user_prompt)
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    print_farewell()
                    break

                prompt = user_input.strip()
                if not prompt:
                    continue
                if _is_exit_command(prompt):
                    console.print()
                    print_farewell()
                    break
                if _is_help_command(prompt):
                    print_help()
                    continue

                try:
                    reset_turn_permissions()
                    await client.query(prompt)
                    async for message in client.receive_response():
                        if hasattr(message, "session_id") and message.session_id:
                            _save_session_id(message.session_id)
                        if isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, ThinkingBlock) and block.thinking:
                                    if os.getenv("SHOW_THINKING", "false").lower() in ("true", "1", "yes"):
                                        print_thinking(block.thinking)
                                elif isinstance(block, TextBlock) and block.text:
                                    print_assistant_message(block.text)
                        elif isinstance(message, ResultMessage) and message.is_error and message.result:
                            print_error(message.result)
                except Exception as exc:
                    print_error(str(exc))
    except Exception as exc:
        print_error(f"Failed to initialize agent: {exc}")
