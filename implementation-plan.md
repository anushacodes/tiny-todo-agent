# Implementation Plan: Tiny Todo Agent (Claude Agent SDK)

A minimal, incremental local CLI where you maintain a tiny todo list, and Claude is allowed to inspect, modify, and reason about it. Built directly with the **Claude Agent SDK**, following official SDK documentation and best practices.

---

## SDK Configuration & OpenRouter

The agent is configured directly using `ClaudeAgentOptions` in `app.py`.

To support OpenRouter or direct Anthropic endpoints without extra boilerplate:
- `ANTHROPIC_BASE_URL="https://openrouter.ai/api"` (when using OpenRouter)
- `ANTHROPIC_AUTH_TOKEN="<your-openrouter-api-key>"`
- `ANTHROPIC_API_KEY=""`

Environment variables from `.env` are passed directly into `ClaudeAgentOptions(env=...)`.

---

## Project Structure

```text
tiny-todo-agent/
│
├── app.py                      # Ultra-thin CLI entry point (11 lines)
├── todos.json                  # Tiny JSON task database
├── agent.log                   # Audit log populated by SDK hooks
├── mcp_server.py               # Standalone MCP server (Phase 5)
├── agent/                      # Modular Python package
│   ├── __init__.py
│   ├── storage.py              # Data models & pure file I/O
│   ├── tools.py                # MCP @tool definitions & SDK server setup
│   ├── permissions.py          # Fine-grained runtime authorization
│   └── agent.py                # Options builder & REPL loop
├── todo-plugin/                # Self-contained plugin bundle (Phase 8)
└── .claude/                    # Project-level configs (Phase 6)
    ├── skills/
    │   └── todo-management/
    │       └── SKILL.md        # Todo conventions & priority rules
    ├── commands/
    │   ├── todos.md            # Slash command /todos
    │   └── prioritize.md       # Slash command /prioritize
    └── agents/
        └── prioritizer.md      # Subagent definition
```

---

## Phased Implementation Plan & Atomic Checklist

### Phase 1: Minimal Agent & File-Backed Todos (User → Claude → Tools → todos.json)
Establish the basic interactive loop where Claude reads and mutates `todos.json` using SDK tools.

- [x] **Step 1.1**: Project setup & SDK options configuration
  - Initialize `pyproject.toml` with `claude-agent-sdk` and `python-dotenv`.
  - Create initial empty `todos.json` (`{"todos": []}`).
  - Configure `.env.example` and `.gitignore`.
- [x] **Step 1.2**: Data model & pure file operations in `app.py`
  - Define `Todo` schema (id, title, status: pending/completed, priority: low/medium/high, created_at).
  - Implement file persistence helpers (`_load_todos()`, `_save_todos()`).
- [x] **Step 1.3**: SDK tool definitions
  - Implement `@tool` functions:
    - `list_todos(status_filter: str | None = None)`
    - `add_todo(title: str, priority: str = "medium")`
    - `complete_todo(todo_id: str)`
    - `delete_todo(todo_id: str)`
  - Register tools via `create_sdk_mcp_server("todo-tools", tools=[...])`.
- [x] **Step 1.4**: Interactive CLI loop in `app.py`
  - Use `ClaudeSDKClient` or streaming `query` with `ClaudeAgentOptions`.
  - Provide a clean interactive prompt (`> `) handling user input and streaming Claude's text output.
- [ ] **Step 1.5**: Phase 1 Verification
  - Add task "learn Redis", list tasks, mark complete, and verify `todos.json` updates.

---

### Phase 2: Fine-Grained Permissions (Read: Auto, Modify: Prompt)
- [x] **Step 2.1**: Implement `can_use_tool` callback in `ClaudeAgentOptions`.
- [x] **Step 2.2**: Auto-allow `list_todos` via `PermissionResultAllow()`.
- [x] **Step 2.3**: Prompt user in CLI for mutating tools (`add_todo`, `complete_todo`, `delete_todo`).
- [ ] **Step 2.4**: Phase 2 Verification.

---

### Phase 3: Lifecycle Observability Hooks (Audit Logging to `agent.log`)
- [x] **Step 3.1**: Configure clean logger writing to `agent.log`.
- [x] **Step 3.2**: Implement `PreToolUse` hook callback logging tool invocations.
- [x] **Step 3.3**: Implement `PostToolUse` hook callback logging responses.
- [x] **Step 3.4**: Attach hooks via `HookMatcher` in `ClaudeAgentOptions.hooks`.
- [x] **Step 3.5**: Phase 3 Verification.

---

### Phase 4: Multi-Agent Subagent Delegation (Prioritizer)
- [x] **Step 4.1**: Define `prioritizer` subagent via `AgentDefinition`.
- [x] **Step 4.2**: Register subagent in `ClaudeAgentOptions.agents`.
- [x] **Step 4.3**: Phase 4 Verification: evaluate backlog and recommend highest-priority task.

---

### Phase 5: Decoupled MCP Tool Server (`mcp_server.py`)
- [x] **Step 5.1**: Implement standalone stdio MCP server `mcp_server.py`.
- [x] **Step 5.2**: Configure `mcp_servers={"todo-server": {"type": "stdio", "command": "uv", "args": ["run", "python", "mcp_server.py"]}}`.
- [x] **Step 5.3**: Phase 5 Verification.

---

### Phase 6: Project Configuration & Knowledge via `.claude/`
- [x] **Step 6.1**: Create `todo-management` skill (`.claude/skills/todo-management/SKILL.md`).
- [x] **Step 6.2**: Create slash commands `/todos` and `/prioritize` in `.claude/commands/`.
- [x] **Step 6.3**: Move subagent definition to `.claude/agents/prioritizer.md`.
- [x] **Step 6.4**: Enable `setting_sources=["project"]` in `ClaudeAgentOptions`.
- [x] **Step 6.5**: Phase 6 Verification.

---

### Phase 7: Stateful Sessions & Long-Term Memory
- [ ] **Step 7.1**: Implement session ID persistence and `--resume` support in `app.py`.
- [ ] **Step 7.2**: Configure project memory retention for user preferences.
- [ ] **Step 7.3**: Phase 7 Verification.

---

### Phase 8: Plugin Encapsulation & Distribution
- [ ] **Step 8.1**: Structure plugin package (`todo-plugin/`) with manifest.
- [ ] **Step 8.2**: Load plugin via `SdkPluginConfig(type="local", path="./todo-plugin")`.
- [ ] **Step 8.3**: Phase 8 Verification.
