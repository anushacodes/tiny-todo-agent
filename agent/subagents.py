from __future__ import annotations

from claude_agent_sdk import AgentDefinition


def get_agent_definitions() -> dict[str, AgentDefinition]:
    return {
        "prioritizer": AgentDefinition(
            description="Recommends next todo by priority/urgency.",
            prompt="You are a prioritization expert. Use list_todos, pick one best task with brief reasoning.",
            tools=["mcp__todo-server__list_todos"],
            memory="project",
        )
    }
