"""Tiny Todo Agent — CLI for managing personal todos using Claude Agent SDK.

This module provides data models, file storage operations, and the agent
runtime loop for inspecting, modifying, and reasoning about tasks.
This module provides data models, file storage operations, tool definitions,
and an interactive REPL loop using the Claude Agent SDK.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

from claude_agent_sdk import create_sdk_mcp_server, tool
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool,
)
from claude_agent_sdk.types import McpSdkServerConfig
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# constants
TODOS_FILE: Path = Path(os.getenv("TODOS_FILE_PATH", "todos.json"))
DEFAULT_MODEL: str = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")


# environment configuration helper
def _get_sdk_env() -> dict[str, str]:
    """Build subprocess environment dictionary for Claude Agent SDK."""
    env_vars: dict[str, str] = {}
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if openrouter_key or "openrouter.ai" in anthropic_base_url:
        env_vars["ANTHROPIC_BASE_URL"] = anthropic_base_url or "https://openrouter.ai/api"
        env_vars["ANTHROPIC_AUTH_TOKEN"] = openrouter_key
        env_vars["ANTHROPIC_API_KEY"] = ""
    elif anthropic_key:
        env_vars["ANTHROPIC_API_KEY"] = anthropic_key
        if anthropic_base_url:
            env_vars["ANTHROPIC_BASE_URL"] = anthropic_base_url

    return env_vars


# todo schema
class Todo(TypedDict):
    """Data representation of a single todo item."""

    id: int
    title: str
    status: Literal["pending", "completed"]
    priority: Literal["low", "medium", "high"]
    created_at: str


# storage helpers
def _load_todos(file_path: Path = TODOS_FILE) -> list[Todo]:
    """Load todos from the JSON file on disk.

    Returns an empty list if the file does not exist or contains invalid data.
    """
    if not file_path.exists():
        _save_todos([], file_path)
        return []

    try:
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        data: dict[str, Any] = json.loads(content)
        todos = data.get("todos", [])
        if isinstance(todos, list):
            return todos
        return []
    except (json.JSONDecodeError, OSError):
        return []


def _save_todos(todos: list[Todo], file_path: Path = TODOS_FILE) -> None:
    """Save the given list of todos to disk as indented JSON."""
    payload = {"todos": todos}
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# sdk tools
@tool(
    name="list_todos",
    description="List todos from the task database, optionally filtered by status ('pending', 'completed', or 'all').",
    input_schema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["all", "pending", "completed"],
                "description": "Status filter: all, pending, or completed (default: all)",
            }
        },
    },
)
async def list_todos(args: dict[str, Any]) -> dict[str, Any]:
    """List todos filtered by status."""
    todos = _load_todos()
    status_filter = args.get("status", "all")

    if status_filter in ("pending", "completed"):
        filtered = [t for t in todos if t["status"] == status_filter]
    else:
        filtered = todos

    if not filtered:
        msg = f"No todos found (filter: {status_filter})."
    else:
        msg = json.dumps(filtered, indent=2)

    return {"content": [{"type": "text", "text": msg}]}


@tool(
    name="add_todo",
    description="Add a new todo task to the list with an optional priority ('low', 'medium', 'high').",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title or description of the task to add",
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Priority level: low, medium, or high (default: medium)",
            },
        },
        "required": ["title"],
    },
)
async def add_todo(args: dict[str, Any]) -> dict[str, Any]:
    """Add a new task to todos.json."""
    title = str(args.get("title", "")).strip()
    if not title:
        return {
            "content": [{"type": "text", "text": "Error: Todo title cannot be empty."}],
            "is_error": True,
        }

    raw_priority = str(args.get("priority", "medium")).lower()
    priority: Literal["low", "medium", "high"] = (
        raw_priority if raw_priority in ("low", "medium", "high") else "medium"
    )

    todos = _load_todos()
    next_id = max([t["id"] for t in todos], default=0) + 1
    new_todo: Todo = {
        "id": next_id,
        "title": title,
        "status": "pending",
        "priority": priority,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    todos.append(new_todo)
    _save_todos(todos)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Added todo #{new_todo['id']}: '{new_todo['title']}' (priority: {new_todo['priority']})",
            }
        ]
    }


@tool(
    name="complete_todo",
    description="Mark a specific todo item as completed by its numeric ID.",
    input_schema={
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "The numeric ID of the todo to mark complete",
            }
        },
        "required": ["id"],
    },
)
async def complete_todo(args: dict[str, Any]) -> dict[str, Any]:
    """Mark a task as completed in todos.json."""
    todo_id = args.get("id")
    if todo_id is None:
        return {
            "content": [{"type": "text", "text": "Error: Missing required 'id' parameter."}],
            "is_error": True,
        }

    todos = _load_todos()
    target = next((t for t in todos if t["id"] == int(todo_id)), None)
    if not target:
        return {
            "content": [{"type": "text", "text": f"Error: Todo #{todo_id} not found."}],
            "is_error": True,
        }

    target["status"] = "completed"
    _save_todos(todos)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Marked todo #{todo_id} '{target['title']}' as completed.",
            }
        ]
    }


@tool(
    name="delete_todo",
    description="Delete a specific todo item permanently by its numeric ID.",
    input_schema={
        "type": "object",
        "properties": {
            "id": {
                "type": "integer",
                "description": "The numeric ID of the todo to delete",
            }
        },
        "required": ["id"],
    },
)
async def delete_todo(args: dict[str, Any]) -> dict[str, Any]:
    """Delete a task from todos.json."""
    todo_id = args.get("id")
    if todo_id is None:
        return {
            "content": [{"type": "text", "text": "Error: Missing required 'id' parameter."}],
            "is_error": True,
        }

    todos = _load_todos()
    target = next((t for t in todos if t["id"] == int(todo_id)), None)
    if not target:
        return {
            "content": [{"type": "text", "text": f"Error: Todo #{todo_id} not found."}],
            "is_error": True,
        }

    todos = [t for t in todos if t["id"] != int(todo_id)]
    _save_todos(todos)

    return {
        "content": [
            {
                "type": "text",
                "text": f"Deleted todo #{todo_id} '{target['title']}'.",
            }
        ]
    }


# mcp server setup
def create_todo_tools_server() -> McpSdkServerConfig:
    """Create an in-process SDK MCP server hosting all todo tools."""
    return create_sdk_mcp_server(
        name="todo-tools",
        version="1.0.0",
        tools=[list_todos, add_todo, complete_todo, delete_todo],
    )


if __name__ == "__main__":
    import asyncio
# agent configuration
def build_agent_options() -> ClaudeAgentOptions:
    """Construct options for the Claude Agent SDK."""
    tools_server = create_todo_tools_server()
    allowed_tools = [
        "mcp__todo-tools__list_todos",
        "mcp__todo-tools__add_todo",
        "mcp__todo-tools__complete_todo",
        "mcp__todo-tools__delete_todo",
    ]

    async def _test_tools() -> None:
        print("Testing tools directly...")
        # test adding
        add_res = await add_todo.handler({"title": "learn Redis", "priority": "high"})
        print("add_todo:", add_res["content"][0]["text"])
    system_prompt = (
        "You are a friendly personal todo assistant. You help the user inspect, "
        "modify, and reason about their tasks using the provided todo tools. "
        "Always use the appropriate todo tool when the user asks to add, list, "
        "complete, or delete tasks. Keep responses concise, helpful, and direct."
    )

        # test listing
        list_res = await list_todos.handler({})
        print("list_todos:", list_res["content"][0]["text"])
    return ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        mcp_servers={"todo-tools": tools_server},
        allowed_tools=allowed_tools,
        env=_get_sdk_env(),
    )

        # test completing
        comp_res = await complete_todo.handler({"id": 1})
        print("complete_todo:", comp_res["content"][0]["text"])

        # test deleting
        del_res = await delete_todo.handler({"id": 1})
        print("delete_todo:", del_res["content"][0]["text"])
# interactive cli loop
async def run_cli() -> None:
    """Run the interactive CLI session."""
    print("=" * 60)
    print("🧸 Tiny Todo Agent (Claude Agent SDK)")
    print("Type a request (e.g. 'Add learn Redis', 'List my todos')")
    print("Type 'exit' or 'quit' to close.")
    print("=" * 60)

        # verify server creation
        server = create_todo_tools_server()
        print(f"Created MCP server: {server['name']}")
    options = build_agent_options()

    asyncio.run(_test_tools())
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
                        elif isinstance(message, ResultMessage):
                            if message.is_error and message.result:
                                print(f"\n[Agent Error]: {message.result}")
                except Exception as exc:
                    print(f"\n[Error during query]: {exc}")
    except Exception as exc:
        print(f"\nFailed to initialize Claude Agent SDK: {exc}")


if __name__ == "__main__":
    asyncio.run(run_cli())
