# Python Engineering Rulebook

## Purpose

This rulebook defines the coding style, engineering practices, architecture preferences, command conventions, documentation standards, Git workflow, and general development behavior that the coding agent MUST follow.

These rules are intentionally **project-agnostic**.

The agent should reproduce the engineering quality and consistency of a well-structured production Python repository, rather than copying the domain or architecture of any particular project.

---

# 1. Core Engineering Philosophy

## 1.1 Prefer simple, explicit code

Write code that another engineer can understand quickly.

Prefer:

```python
def get_model() -> BaseChatModel:
    settings = get_settings()

    if settings.provider == "openai":
        return ChatOpenAI(
            model=settings.model_name,
            temperature=settings.temperature,
        )

    if settings.provider == "anthropic":
        return ChatAnthropic(
            model=settings.model_name,
            temperature=settings.temperature,
        )

    raise ValueError(f"Unknown provider: {settings.provider!r}")
```

over:

```python
def get_model():
    return PROVIDERS[settings.provider](**settings.model_config)
```

unless the abstraction genuinely reduces complexity.

### Rules

- Prefer readable control flow over clever abstractions.
- Do not introduce abstractions simply because they are theoretically reusable.
- Avoid unnecessary design patterns.
- Do not create classes when a function is sufficient.
- Do not create utility modules for one-off operations.
- Prefer explicit dependencies over hidden global state.
- Prefer code that makes the execution path obvious.

---

# 2. Python Version and Language Features

Use modern Python.

### Rules

- Use Python 3.11+ syntax unless the project specifies otherwise.
- Prefer built-in generic types:

```python
list[str]
dict[str, int]
tuple[str, ...]
```

instead of:

```python
List[str]
Dict[str, int]
Tuple[str, ...]
```

- Use `X | None` rather than `Optional[X]`.
- Use `from __future__ import annotations` when useful for forward references and consistent typing.
- Use structural typing and protocols when they provide meaningful decoupling.
- Use dataclasses, enums, TypedDicts, or Pydantic models when they make data contracts clearer.

---

# 3. Imports

Imports MUST be grouped and ordered consistently.

Preferred structure:

```python
from __future__ import annotations

import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings
from app.services.worker import run_job
```

### Rules

1. `__future__` imports first.
2. Standard library imports second.
3. Third-party imports third.
4. Local application imports last.
5. Separate groups with one blank line.
6. Do not use wildcard imports.
7. Keep imports at module scope unless a lazy import is intentionally required.

---

# 4. Module Structure

Every Python module should have an obvious structure.

Preferred order:

```text
module docstring
↓
future imports
↓
standard-library imports
↓
third-party imports
↓
local imports
↓
constants
↓
types / models
↓
private helper functions
↓
public functions
↓
classes
↓
entry points / orchestration
```

Do not randomly interleave unrelated functions, constants, and imports.

---

# 5. Module Docstrings

Important modules should explain their responsibility.

Example:

```python
"""Model factory — selects the configured language-model provider.

The factory keeps provider-specific construction in one place so the rest
of the application can depend on the common BaseChatModel interface.
"""
```

A module docstring should explain:

- what the module does;
- why it exists;
- important architectural responsibility;
- unusual implementation constraints.

Do not write meaningless docstrings such as:

```python
"""Utils."""
```

---

# 6. Naming

Use names that describe behavior.

## Variables

Prefer:

```python
job_id
previous_result
revision_instruction
model_provider
request_timeout
```

Avoid:

```python
x
data
thing
obj
tmp
stuff
```

unless the scope genuinely makes the short name obvious.

## Functions

Functions should generally be verbs:

```python
get_model()
build_orchestrator()
assemble_result()
parse_thread()
seed_files()
run_job()
```

Avoid:

```python
model()
result()
thing()
handler()
```

when the behavior is more specific.

## Private functions

Use `_` for implementation details:

```python
def _seed_files(...):
    ...

def _parse_thread(...):
    ...
```

Do not expose helpers publicly unless they are actually part of the module's API.

---

# 7. Functions

Functions should have one obvious responsibility.

Good:

```python
def _workspace(job_id: str) -> str:
    return f"/workspace/{job_id}"
```

Good:

```python
def _parse_thread(markdown: str) -> list[str]:
    ...
```

Bad:

```python
def process_everything(...):
    # validates input
    # connects to database
    # calls API
    # transforms data
    # sends email
    # logs metrics
    # saves results
```

If a function contains several independent responsibilities, extract meaningful helpers.

---

# 8. Function Size

Do not impose an artificial line limit.

Instead:

> A function should be short enough that its behavior can be understood without mentally simulating a large amount of unrelated logic.

Large functions are acceptable when they represent a single orchestration workflow.

For example:

```python
def run_job(...):
    start_time = time.time()

    agent = build_agent()
    files = seed_files(...)
    emit("running", "agent")

    for chunk in agent.stream(...):
        ...

    result = assemble_result(...)

    record_metrics(...)

    return result
```

This is acceptable because the function describes one complete workflow.

---

# 9. Type Hints

Type hints are expected throughout the codebase.

Prefer:

```python
def assemble_result(
    files: dict,
    job_id: str,
    platforms: Iterable[str],
) -> dict:
    ...
```

over:

```python
def assemble_result(files, job_id, platforms):
    ...
```

### Rules

- Public functions MUST have parameter and return annotations.
- Important private functions SHOULD also be typed.
- Use meaningful types instead of `Any`.
- Use `Any` only when the external library or dynamic boundary genuinely requires it.
- Do not add complicated typing solely to satisfy a type checker.

---

# 10. `Any`

`Any` is an escape hatch, not a default type.

Bad:

```python
def process(data: Any) -> Any:
    ...
```

Better:

```python
def process(data: dict[str, str]) -> ProcessedResult:
    ...
```

If an external framework requires dynamic values:

```python
def _generate(
    messages: list[BaseMessage],
    stop: list[str] | None = None,
    run_manager: Any = None,
    **kwargs: Any,
) -> ChatResult:
    ...
```

Using `Any` at an integration boundary is acceptable when the underlying library itself is dynamic.

---

# 11. Configuration

Configuration belongs in one centralized location.

Prefer:

```python
class Settings:
    DATABASE_URL: str = os.getenv(...)
    REDIS_URL: str = os.getenv(...)
    MODEL_PROVIDER: str = os.getenv(...)
```

with:

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

The repository uses centralized environment-based configuration and caches the settings object. 

### Rules

- Do not scatter `os.getenv()` throughout business logic.
- Do not hard-code secrets.
- Do not hard-code deployment-specific infrastructure.
- Environment variables should control deployment-specific behavior.
- Defaults should be safe for local development.
- Keep configuration names explicit and descriptive.

---

# 12. Constants

Constants belong near the top of the module.

Example:

```python
SKILLS_ROOT = "/skills"
CONTEXT_PATH = "/context/AGENTS.md"
DEFAULT_TIMEOUT_SECONDS = 30
```

Use uppercase names for module-level constants.

Avoid magic values:

```python
if attempts > 3:
```

Prefer:

```python
MAX_RETRIES = 3

if attempts > MAX_RETRIES:
```

---

# 13. Comments

Comments should explain **why**, not merely **what**.

Bad:

```python
# Increment counter
counter += 1
```

Good:

```python
# Keep the retry budget separate from request attempts so transient
# provider failures do not exhaust the user's request quota.
counter += 1
```

Use comments when:

- behavior is non-obvious;
- an external library has an unusual constraint;
- an architectural decision needs explanation;
- an implementation workaround is required.

Do not narrate obvious code.

---

# 14. Section Comments

Never use banner delimiter comments like:

```python
# --------------------------------------------------------------------------- #
# Public Accessor
# --------------------------------------------------------------------------- #
```

Instead, keep comments minimal, clean, and single-line:

```python
# public accessor
```

Do not reference this rulebook or its sections in source code or docstrings.
When using the Claude Agent SDK, official Claude SDK best practices and conventions take precedence and override general guidelines.

---

# 15. Docstrings

Use docstrings for public functions and non-obvious helpers.

Good:

```python
def assemble_result(
    files: dict,
    job_id: str,
    platforms: Iterable[str],
) -> dict:
    """Convert the finished workspace into the API response."""
```

For more complicated behavior, document important semantics:

```python
def run_job(...):
    """Run the full pipeline for one job.

    `on_progress` receives coarse status updates as the workspace fills.
    """
```

Do not write docstrings that simply repeat the function name.

---

# 16. Error Handling

Errors should be explicit and useful.

Prefer:

```python
raise ValueError(f"Unknown MODEL_PROVIDER: {provider!r}")
```

over:

```python
raise Exception("bad provider")
```

### Rules

- Raise specific exception types.
- Include useful context in error messages.
- Do not silently swallow exceptions.
- Do not use broad `except Exception` unless there is a deliberate boundary-level reason.
- Handle errors close to the layer that can meaningfully recover from them.
- Let unexpected errors propagate rather than hiding bugs.

---

# 17. External Integrations

Keep provider-specific logic isolated.

For example:

```text
app/
├── agent/
│   ├── model.py
│   ├── cache.py
│   └── tools.py
```

The repository's model factory keeps Ollama, Groq, OpenAI, and Anthropic construction in one module instead of spreading provider-specific code throughout the application. 

### Rule

When integrating multiple implementations of the same concept:

```text
application code
       ↓
common interface
       ↓
provider-specific implementation
```

not:

```text
application code
 ├── if OpenAI
 ├── if Anthropic
 ├── if Groq
 ├── if Ollama
 ├── if ...
 └── ...
```

throughout the entire codebase.

---

# 18. Dependency Direction

Keep dependencies flowing in one direction.

Preferred:

```text
API
 ↓
service / orchestration
 ↓
domain logic
 ↓
infrastructure
```

Avoid circular dependencies such as:

```text
service → API → service
```

or:

```text
model → config → model
```

If two modules need each other, reconsider the boundary.

---

# 19. Separate Orchestration From Implementation

High-level functions should describe the workflow.

Example:

```python
def run_job(...):
    files = seed_files(...)
    agent = build_orchestrator()

    result = execute_pipeline(agent, files)

    return assemble_result(result)
```

The high-level function should read almost like a description of the system.

Implementation details should live in helpers.

---

# 20. Prefer Pure Helpers Where Practical

Keep transformation logic independent from I/O.

Example:

```python
def parse_thread(markdown: str) -> list[str]:
    ...
```

is preferable to a function that:

```text
reads file
→ parses file
→ modifies database
→ logs
→ returns result
```

Pure functions are easier to test and reason about.

---

# 21. Side Effects

Push side effects toward system boundaries.

Side effects include:

- filesystem writes;
- database writes;
- network calls;
- Redis operations;
- LLM calls;
- subprocess execution;
- environment access.

Prefer:

```text
input
 ↓
pure transformation
 ↓
result
 ↓
side effect
```

rather than mixing every operation into one function.

---

# 22. Caching

Caching should be intentional.

Good cache boundaries include:

```text
LLM responses
expensive external API calls
computed immutable data
frequently requested state
```

Do not introduce caching without identifying:

1. what is expensive;
2. what makes the result reusable;
3. cache invalidation rules;
4. TTL;
5. whether stale data is acceptable.

The repository uses Redis for response caching and explicitly centralizes cache setup.

---

# 23. Async and Background Work

Use background workers when work is:

- slow;
- CPU-intensive;
- LLM-intensive;
- network-heavy;
- retryable;
- unsuitable for an HTTP request lifecycle.

The repository uses FastAPI for request handling and Celery + Redis for asynchronous execution.

Do not make an HTTP request wait synchronously for a long-running pipeline if the system can return a job identifier instead.

---

# 24. API Design

API handlers should remain thin.

Prefer:

```python
@router.post("/generate")
def generate(request: GenerateRequest) -> GenerateResponse:
    job_id = service.enqueue(request)
    return GenerateResponse(job_id=job_id)
```

Do not put:

- business logic;
- complex database queries;
- LLM orchestration;
- long workflows

directly inside route handlers.

---

# 25. Data Validation

Validate at system boundaries.

Examples:

```text
HTTP request
CLI input
environment variables
external API responses
database records
```

Once validated, internal code should be able to trust the established contract.

---

# 26. Filesystem Operations

Use `pathlib.Path`.

Prefer:

```python
path = ROOT / "data" / filename
text = path.read_text(encoding="utf-8")
```

over:

```python
path = ROOT + "/data/" + filename
```

Always specify encoding for text files:

```python
path.read_text(encoding="utf-8")
path.write_text(content, encoding="utf-8")
```

---

# 27. File Organization

Organize files around responsibilities.

Example:

```text
app/
├── api/
├── services/
├── models/
├── repositories/
├── config.py
├── worker.py
└── main.py
```

Avoid giant files containing the entire application.

However:

> Do not split code into dozens of tiny files merely to make the tree look sophisticated.

A file should exist because it represents a meaningful responsibility.

---

# 28. Public vs Private APIs

Make the distinction obvious.

Public:

```python
def run_job(...):
    ...
```

Internal:

```python
def _seed_files(...):
    ...
```

If a helper is not intended for external use, prefix it with `_`.

---

# 29. Lazy Imports

Lazy imports are allowed when they solve a real problem.

For example:

```python
if provider == "openai":
    from langchain_openai import ChatOpenAI
```

This is appropriate when:

- the dependency is optional;
- importing it globally would unnecessarily require the package;
- different runtime configurations use different providers;
- startup/import cost matters.

Do not use lazy imports randomly.

---

# 30. Dependency Management

Use `uv` for Python dependency management when the project uses `uv`.

Typical commands:

```bash
uv sync
uv add <package>
uv remove <package>
uv lock
uv run <command>
```

The repository explicitly uses `uv sync` for dependency installation and `uv run` for application commands.

### Critical rule

When modifying dependencies:

```text
pyproject.toml
        ↓
uv lock
        ↓
commit both
```

Do not manually edit `uv.lock`.

The repository's development workflow explicitly requires keeping the lockfile synchronized when dependencies change.

---

# 31. Running Python

Prefer:

```bash
uv run python script.py
```

instead of:

```bash
python script.py
```

Prefer:

```bash
uv run pytest
```

instead of:

```bash
pytest
```

Prefer:

```bash
uv run uvicorn main:app --reload
```

instead of assuming the environment's global executable is correct.

This makes the execution environment reproducible.

---

# 32. Command Style

Commands should be:

- explicit;
- reproducible;
- copy-pasteable;
- scoped to the project's environment.

Good:

```bash
uv run celery -A app.worker.celery_app worker --loglevel=info
```

Good:

```bash
uv run uvicorn main:app --reload --port 8000
```

Avoid vague instructions such as:

```text
Run the backend.
```

Instead provide the exact command.

---

# 33. Makefile / Task Shortcuts

For projects with multiple recurring commands, expose useful shortcuts.

Example:

```makefile
dev:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

worker:
	uv run celery -A app.worker.celery_app worker --loglevel=info
```

Do not create shortcuts for commands that are rarely used.

---

# 34. Environment Variables

Use `.env.example`.

The repository keeps configuration templates separate from actual secrets.

Rules:

- `.env` MUST NOT be committed.
- `.env.example` SHOULD document required variables.
- Never place real API keys in source code.
- Never print secrets in logs.
- Provide safe local-development defaults where appropriate.

---

# 35. Logging

Logs should describe events, not dump arbitrary objects.

Good:

```python
logger.info(
    "Job completed",
    extra={
        "job_id": job_id,
        "platforms": platforms,
    },
)
```

Avoid:

```python
print("stuff happened")
```

Use `print()` only for deliberate CLI output or extremely small scripts.

---

# 36. Observability

Important workflows should expose enough information to debug them.

Track things such as:

```text
request/job ID
duration
status
provider
operation
failure reason
```

The repository associates tracing information with `job_id`, execution time, platforms, and success metadata. 

---

# 37. Tests

Tests should target behavior, not implementation trivia.

Prefer:

```python
def test_parse_thread_returns_numbered_entries():
    ...
```

over testing private implementation details.

Test:

- happy paths;
- edge cases;
- invalid inputs;
- failure behavior;
- important integration boundaries.

Do not add tests that merely increase coverage numbers without protecting behavior.

---

# 38. Testing Before Declaring Completion

The agent MUST NOT say:

> "Done."

until it has verified the relevant code.

At minimum:

```bash
uv run pytest
```

and, when applicable:

```bash
uv run ruff check .
uv run ruff format --check .
```

For applications:

```bash
uv run <application-specific-smoke-test>
```

For APIs, exercise important endpoints.

For CLI applications, actually execute the CLI.

For infrastructure changes, validate the configuration.

---

# 39. Verification Hierarchy

Use the cheapest useful verification first.

```text
1. Syntax / import check
        ↓
2. Formatter / linter
        ↓
3. Unit tests
        ↓
4. Integration tests
        ↓
5. Application smoke test
        ↓
6. Full system verification
```

Do not run expensive end-to-end tests when a simple unit test can identify the issue.

---

# 40. Avoid Premature Abstraction

Do not create:

```text
BaseService
BaseRepository
BaseManager
BaseFactory
AbstractProcessor
GenericHandler
```

unless there is a concrete need.

Three similar lines of code are often preferable to an abstraction that obscures behavior.

Abstract when:

- multiple implementations actually exist;
- dependency inversion is useful;
- behavior varies independently;
- testing requires substitution;
- the abstraction represents a real domain concept.

---

# 41. Avoid Clever One-Liners

Prefer:

```python
if previous_result:
    chunks = build_previous_result(previous_result)
else:
    chunks = []
```

over deeply nested comprehensions or expressions that require careful parsing.

Readable code beats compact code.

---

# 42. Comprehensions

Use comprehensions for simple transformations.

Good:

```python
names = [item.name for item in items]
```

Avoid:

```python
result = {
    transform(x): normalize(y)
    for x, y in source.items()
    if validate(x)
    if ...
}
```

If the comprehension needs explanation, use a loop.

---

# 43. Mutable State

Avoid unnecessary mutation.

Prefer:

```python
result = build_result(data)
return result
```

over creating and repeatedly mutating shared global state.

Mutation is acceptable when it makes an algorithm clearer or is required by a framework.

---

# 44. Global State

Avoid mutable globals.

Bad:

```python
CURRENT_USER = None
CACHE = {}
```

Prefer:

```python
cache = RedisCache(...)
```

and inject it where needed.

Cached configuration is acceptable when intentionally encapsulated:

```python
@lru_cache
def get_settings():
    return Settings()
```

---

# 45. Singletons

Do not create singleton classes just because "there should only be one."

Prefer:

- dependency injection;
- cached factories;
- application lifecycle management.

The repository uses `@lru_cache` for intentionally reused construction such as settings and orchestrator creation. 

---

# 46. Comments Around Architectural Decisions

If code contains an unusual implementation, explain it immediately where the decision occurs.

Example:

```python
# The framework already provides summarization middleware, so we keep
# task-specific context in files rather than duplicating it in the thread.
```

This is better than putting the explanation only in a distant README.

---

# 47. Documentation

README files should answer:

```text
What is this?
Why does it exist?
What does the architecture look like?
What are the prerequisites?
How do I install it?
How do I run it?
How do I test it?
What configuration is required?
What are the important API endpoints?
How do I contribute?
```

The repository's README follows this general structure: overview → architecture → getting started → commands → API → configuration → development workflow.

---

# 48. README Commands

Commands in documentation MUST be directly executable.

Prefer:

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

over:

```text
Start the FastAPI server.
```

Include comments when a command has an important purpose:

```bash
# Start the worker
uv run celery -A app.worker.celery_app worker --loglevel=info
```

---

# 49. Code Blocks in Markdown

Always specify the language.

Good:

````markdown
```python
def hello() -> str:
    return "hello"
```
````

For shell commands:

````markdown
```bash
uv run pytest
```
````

For configuration:

````markdown
```env
DATABASE_URL=...
```
````

Do not use untyped code blocks unless there is a genuine reason.

---

# 50. Markdown Formatting

Keep Markdown clean.

Rules:

- Blank line around code blocks.
- Consistent heading hierarchy.
- Tables must have aligned columns.
- Avoid giant paragraphs.
- Use bullets for discrete items.
- Use numbered lists for ordered workflows.
- Keep examples copy-pasteable.

The repository has historically included commits specifically correcting Markdown lint issues, including language specifiers and spacing. 

---

# 51. Git Branches

Use descriptive branches.

Preferred:

```text
feat/add-auth
feat/redis-cache
fix/job-timeout
fix/invalid-provider
refactor/model-factory
docs/update-setup
```

The repository's documented workflow uses:

```text
feat/<short-name>
```

for feature branches.

---

# 52. Commit Size

A commit should represent one coherent change.

Good:

```text
Add Redis response cache
```

followed by:

```text
Add cache tests
```

if those are intentionally separate.

Avoid commits containing:

```text
new feature
+ unrelated refactor
+ README rewrite
+ formatting changes
+ dependency upgrade
```

unless they are genuinely inseparable.

---

# 53. Commit Messages

Use concise, descriptive imperative-style messages.

Preferred:

```text
feat: add Redis response cache
fix: handle missing job result
refactor: extract model factory
docs: update local setup
test: cover invalid provider
chore: update dependencies
```

If the project explicitly adopts Conventional Commits, use:

```text
type(scope): description
```

Examples:

```text
feat(api): add job status endpoint
fix(worker): handle task retries
refactor(agent): isolate provider selection
test(agent): cover revision workflow
docs(readme): update development setup
chore(deps): update langchain
```

### Important

The reference repository does **not** consistently follow Conventional Commits. Its history contains informal messages such as `Uploading dev phase 1`, `updating readme`, and `Updating developement phase`.

Therefore, this rulebook intentionally improves upon the repository rather than copying that inconsistency.

---

# 54. Commit Message Rules

A commit message should answer:

> What changed?

Not:

> What was I doing?

Bad:

```text
working on stuff
changes
update
fixes
development
```

Good:

```text
fix: handle missing cached result
```

Better:

```text
fix(worker): preserve job status when task fails
```

---

# 55. Commit Body

Use a commit body when the change is non-trivial.

Example:

```text
feat(agent): add provider-specific model factory

Keep provider construction in one module so the orchestration layer
does not depend on individual LLM integrations.
```

Do not write an enormous essay for a small change.

---

# 56. Co-Authored-By

Only add `Co-Authored-By` metadata when it is genuinely required by the project's workflow.

Do not automatically add fake attribution.

The repository contains AI-assisted commits with:

```text
Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

but this should be treated as repository-specific history rather than a universal requirement.

---

# 57. Pull Requests

A PR should explain:

```text
What changed?
Why?
How was it tested?
Are there architectural implications?
```

Keep PRs focused.

Do not mix unrelated refactoring into feature PRs.

---

# 58. Change Discipline

Before editing code:

1. Understand the existing structure.
2. Find the module responsible for the behavior.
3. Read surrounding code.
4. Identify existing patterns.
5. Make the smallest coherent change.
6. Run verification.
7. Review the resulting diff.

Do not immediately create new files.

---

# 59. Reuse Existing Patterns

Before introducing a new pattern, search the repository.

For example:

```text
How does this repository currently handle configuration?
How does it create clients?
How does it validate input?
How does it report errors?
How are background jobs structured?
How are tests organized?
```

If an existing pattern is good, reuse it.

Consistency is more valuable than introducing a theoretically superior pattern in one isolated location.

---

# 60. No Duplicate Logic

If the same meaningful logic appears in multiple places, consider extracting it.

Bad:

```python
# route A
provider = settings.provider.lower()

# route B
provider = settings.provider.lower()

# worker
provider = settings.provider.lower()
```

Prefer:

```python
provider = get_provider()
```

But do not extract trivial one-line expressions merely to eliminate textual duplication.

---

# 61. Dependency Injection

When a component needs an external dependency, make that dependency visible.

Prefer:

```python
def process_job(
    job: Job,
    repository: JobRepository,
) -> Result:
    ...
```

over:

```python
def process_job(job):
    repository = GlobalRepository()
```

This makes code:

- easier to test;
- easier to replace;
- easier to understand.

---

# 62. Framework Code vs Business Logic

Framework-specific code should stay near the framework boundary.

For example:

```text
FastAPI
Celery
Redis
SQLAlchemy
LangChain
```

should not leak into every function.

Prefer:

```text
API layer
   ↓
application/service layer
   ↓
domain logic
   ↓
infrastructure adapters
```

---

# 63. External API Boundaries

Wrap external services behind small interfaces.

Instead of:

```python
# throughout the application
openai_client.responses.create(...)
openai_client.responses.create(...)
openai_client.responses.create(...)
```

prefer:

```python
llm.generate(...)
```

with the provider implementation isolated behind it.

This makes provider changes localized.

---

# 64. State Management

State should have an explicit owner.

Every important piece of state should answer:

```text
Who creates it?
Who owns it?
Who mutates it?
How long does it live?
Where is it persisted?
When does it expire?
```

Do not create accidental state through globals or hidden caches.

---

# 65. IDs

Use explicit IDs for workflows and distributed operations.

Example:

```python
job_id = uuid.uuid4().hex[:12]
```

Use IDs consistently in:

- logs;
- traces;
- database records;
- queue messages;
- API responses.

---

# 66. Time

Use timezone-aware timestamps for persisted or distributed data.

Do not casually rely on local machine time.

For duration measurement, use:

```python
start = time.monotonic()
...
elapsed = time.monotonic() - start
```

For persisted timestamps, use explicit UTC-aware datetimes.

---

# 67. Security

Never:

- commit API keys;
- log credentials;
- expose secrets through API responses;
- trust user input blindly;
- execute arbitrary shell commands from untrusted input;
- construct SQL using string interpolation.

Validate and sanitize at boundaries.

---

# 68. Secrets

Never write:

```python
OPENAI_API_KEY = "sk-..."
```

Use:

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
```

and preferably centralize access through the configuration layer.

---

# 69. Database Code

Database access should be isolated.

Avoid embedding large SQL queries directly inside API handlers.

Prefer:

```text
route
 ↓
service
 ↓
repository
 ↓
database
```

Keep transactions explicit.

---

# 70. Redis / Cache Code

Do not mix cache implementation with business logic.

Prefer:

```python
cached = cache.get(key)

if cached is not None:
    return cached

result = expensive_operation(...)
cache.set(key, result)

return result
```

with the cache implementation isolated.

---

# 71. LLM / Agent Code

When working with LLM systems:

- separate model selection from orchestration;
- separate prompts from business logic where practical;
- isolate tools;
- keep context boundaries explicit;
- avoid passing unnecessary state;
- make expensive operations observable;
- make retries explicit;
- avoid hiding LLM calls inside unrelated utilities.

The reference project explicitly separates the model factory, orchestration, tools, skills, context, and agent execution. 

---

# 72. Prompt / Agent Instructions

Agent instructions should be explicit.

Prefer:

```text
1. Read X.
2. Produce Y.
3. Do not modify Z.
4. Save output to A.
5. Verify B.
```

over:

```text
Do the task carefully.
```

Agent workflows should define:

- input;
- allowed tools;
- files to read;
- files to modify;
- expected output;
- constraints;
- verification.

---

# 73. Context Engineering

For agentic applications, do not dump all available information into every context.

Prefer:

```text
stable context
+
task-specific context
+
role-specific instructions
+
required artifacts
```

The reference repository deliberately seeds stable context, per-job briefs, and skill-specific material rather than giving every subagent the entire state. 

---

# 74. Progressive Disclosure

Load information only when needed.

Instead of:

```text
every agent receives every document
```

prefer:

```text
agent
 ↓
role
 ↓
required skill
 ↓
required files
```

This reduces:

- context size;
- cognitive load;
- accidental coupling;
- irrelevant information.

---

# 75. Agent Roles

When building multi-agent systems:

Each agent should have:

```text
one clear responsibility
one expected output
one defined input
```

Avoid:

```text
"general-purpose agent that does everything"
```

unless that is genuinely the intended architecture.

---

# 76. Orchestrators

An orchestrator coordinates.

It should generally:

```text
read state
↓
delegate work
↓
check state
↓
delegate next work
↓
verify completion
↓
return result
```

It should not perform every task itself.

The reference orchestrator explicitly describes itself as coordination rather than content generation and delegates extraction, writing, and review. 

---

# 77. State Over Conversation

For long-running workflows, prefer durable artifacts over enormous conversational context.

For example:

```text
/workspace/job-id/
    brief.md
    extracted.md
    draft.md
    review.md
```

rather than passing every previous output through every agent message.

This makes workflows:

- inspectable;
- resumable;
- debuggable;
- easier to test.

---

# 78. Verification Loops

For non-trivial work:

```text
implement
↓
run
↓
inspect
↓
fix
↓
run again
```

Do not assume the first implementation is correct.

---

# 79. Diff Review

After making changes, inspect the diff.

Ask:

```text
Did I change only what I intended?
Did I accidentally modify unrelated files?
Did I introduce dead code?
Did I add unnecessary abstractions?
Did I leave debugging code?
Did formatting change unrelated sections?
```

---

# 80. Dead Code

Do not leave:

```python
# old implementation
# def old_function(...):
#     ...
```

or unused imports, variables, classes, or files.

Delete obsolete code unless there is a specific historical reason to preserve it.

Git already provides history.

---

# 81. TODOs

Do not leave vague TODOs.

Bad:

```python
# TODO: fix this
```

Better:

```python
# TODO: replace polling with Redis pub/sub after the worker protocol is stable.
```

TODOs should describe a concrete future action.

---

# 82. Debugging Code

Never leave:

```python
print(data)
breakpoint()
pdb.set_trace()
```

in production code unless intentionally required.

Remove temporary instrumentation before committing.

---

# 83. Formatting

Use one formatter consistently across the repository.

Preferred modern Python baseline:

```bash
uv run ruff format .
```

Do not manually fight the formatter.

After formatting:

```bash
uv run ruff check .
```

Formatting and linting should be deterministic.

---

# 84. Linting

Use a linter consistently.

Recommended baseline:

```bash
uv run ruff check .
```

Fix actual issues rather than blindly disabling rules.

If a rule is intentionally inappropriate:

```python
# noqa: <specific-rule>
```

should be narrowly scoped and justified.

Do not disable entire categories globally merely to make CI green.

---

# 85. Type Checking

For projects where type safety matters, use:

```bash
uv run mypy .
```

or:

```bash
uv run pyright
```

Do not introduce a type checker merely because another project uses one. Adopt it when the project benefits from static analysis.

---

# 86. Dependency Changes

Before adding a package, ask:

```text
Can the standard library solve this?
Is the dependency maintained?
Does it materially reduce complexity?
Does the project already have an equivalent?
```

Do not add dependencies for trivial functionality.

---

# 87. Dependency Versions

Prefer compatible version constraints appropriate to the project's release strategy.

Keep the lockfile committed for reproducible environments.

Do not casually upgrade many unrelated dependencies during a feature change.

---

# 88. Architecture Changes

Architecture changes require more caution than local changes.

Before changing architecture:

1. Identify the current boundary.
2. Identify the problem.
3. Explain why the current design is insufficient.
4. Identify affected modules.
5. Make the smallest viable architectural change.
6. Verify all affected paths.

---

# 89. Avoid Architecture Theater

Do not add:

```text
microservices
queues
event buses
repositories
factories
dependency injection frameworks
Kubernetes
```

simply because they sound production-grade.

Use complexity only when the problem requires it.

---

# 90. Production Mindset

"Production quality" means:

```text
clear behavior
+
explicit boundaries
+
predictable errors
+
testability
+
observability
+
reproducibility
+
maintainability
```

It does NOT mean:

```text
maximum number of abstractions
```

---

# 91. Agent Development Workflow

For every coding task, the agent should follow:

## Phase 1 — Understand

```text
Inspect repository
↓
Identify relevant files
↓
Read existing implementation
↓
Identify existing patterns
```

## Phase 2 — Plan

```text
Define intended change
↓
Identify affected files
↓
Avoid unnecessary changes
```

## Phase 3 — Implement

```text
Make the smallest coherent change
↓
Follow existing conventions
↓
Keep interfaces explicit
```

## Phase 4 — Verify

```text
Format
↓
Lint
↓
Test
↓
Smoke test if applicable
```

## Phase 5 — Review

```text
Inspect diff
↓
Remove dead code
↓
Check error handling
↓
Check types
↓
Check documentation
```

## Phase 6 — Commit

```text
Create one focused commit
↓
Use a descriptive commit message
```

---

# 92. Agent MUST NOT

The coding agent MUST NOT:

- rewrite unrelated files;
- introduce unnecessary frameworks;
- create abstractions without a concrete use;
- ignore existing repository conventions;
- hard-code credentials;
- leave debugging statements;
- silently swallow errors;
- use `Any` everywhere;
- skip type hints on important APIs;
- skip verification;
- modify lockfiles manually;
- make broad dependency upgrades without reason;
- claim success without running appropriate checks;
- create giant functions when responsibilities can be separated;
- create dozens of tiny files merely for organizational appearance.

---

# 93. Agent SHOULD

The coding agent SHOULD:

- prefer simple code;
- reuse existing patterns;
- make dependencies explicit;
- keep side effects at boundaries;
- use modern Python typing;
- centralize configuration;
- isolate integrations;
- document non-obvious decisions;
- keep commits focused;
- make commands reproducible;
- verify changes before completion;
- inspect diffs;
- optimize for maintainability over cleverness.

---

# 94. Definition of Done

A task is complete only when:

- [ ] The requested behavior is implemented.
- [ ] Existing behavior remains intact unless intentionally changed.
- [ ] Code follows repository conventions.
- [ ] Types are present where appropriate.
- [ ] Errors are handled explicitly.
- [ ] No secrets are introduced.
- [ ] No debug code remains.
- [ ] Formatting passes.
- [ ] Linting passes.
- [ ] Relevant tests pass.
- [ ] Relevant smoke tests pass.
- [ ] Documentation is updated when behavior or setup changes.
- [ ] The diff contains no unrelated modifications.
- [ ] The commit message clearly describes the change.

---

# 95. The Golden Rule

When uncertain, prefer:

> **The simplest implementation that makes the behavior obvious, keeps boundaries explicit, is easy to test, and fits the patterns already established by the repository.**

Do not optimize for cleverness.

Do not optimize for line count.

Do not optimize for abstraction count.

Optimize for:

```text
clarity
+
correctness
+
maintainability
+
testability
+
operability
```

That is the standard the coding agent should reproduce across projects.