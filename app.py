"""Tiny Todo Agent — CLI for managing personal todos using Claude Agent SDK.

This module provides data models, file storage operations, and the agent
runtime loop for inspecting, modifying, and reasoning about tasks.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv

# load environment variables
load_dotenv()

# constants
TODOS_FILE: Path = Path(os.getenv("TODOS_FILE_PATH", "todos.json"))


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


if __name__ == "__main__":
    todos = _load_todos()
    print(f"Loaded {len(todos)} todos from {TODOS_FILE}.")

