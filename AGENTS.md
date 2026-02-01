# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Project Overview

**olink** is a CLI tool that opens external URLs related to your project (PyPI, npm, GitHub, etc.).

- **Stack**: Python 3.14+, Typer, UV (package manager).
- **Goal**: Simplicity, speed, and helpfulness.

## Build & Run Commands

```bash
uv sync                 # Install dependencies
uv run olink <target>   # Run CLI
uv run pytest           # Run all tests
uv run pytest -v        # Verbose output
```

**Running Specific Tests:**

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_cli.py::TestCLIDryRun
uv run pytest tests/test_cli.py::TestCLIDryRun::test_dry_run_pypi
```

## Code Style

- **Formatting**: Follow PEP 8. Use `ruff` defaults if available (sorted imports, etc.).
- **Types**: MANDATORY. Use type hints for all arguments and return values.
- **Naming**:
  - Classes: `PascalCase` (e.g., `PyPITarget`)
  - Functions/Vars: `snake_case` (e.g., `get_url`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `PLATFORM_URLS`)
  - Private: Prefix with `_` (e.g., `_read_config`)
- **Docstrings**: Document **why**, not **what**. Required for public interfaces.
- **Error Handling**:
  - Use custom exceptions from `olink.core.exceptions`.
  - Hierarchy: `OlinkError` > `NotGitRepoError`, `UnknownTargetError`, etc.
  - Never raise generic `Exception`.

## Testing Strategy

- **Fixtures** (`tests/conftest.py`):
  - `temp_dir`: Empty temp directory.
  - `temp_git_repo[_https|_gitlab]`: Git repos with various remotes.
  - `temp_pyproject`/`temp_package_json`/`temp_cargo_toml`/`temp_go_mod`: Project files.
- **Structure**: Group tests in classes (e.g., `class TestCLIDryRun:`).
- **Mocking**: Mock external side effects (browser launch, git push).

## Architecture Patterns

1.  **Data Over Classes**: If it's just mapping inputs to outputs, use a `dict`.

    ```python
    # Good
    PLATFORM_URLS = {"github": "/issues", "gitlab": "/-/issues"}
    ```

2.  **Target Pattern**: All targets inherit from `Target` and implement `get_url(cwd)`.

3.  **File I/O Over Subprocess**: Read config files directly instead of spawning git/npm commands.
    ```python
    # Good: config.read("git/config")
    # Bad: subprocess.run(["git", "config", ...])
    ```

## Agent Principles

1.  **Regenerability**: Write code so files can be rewritten from scratch without breaking the system. Minimize coupling.
2.  **Structure**: Group code by feature. Avoid shared utilities unless absolutely necessary.
3.  **Simplicity**: Prefer flat, explicit code over abstractions. No metaprogramming.
4.  **Journal**: Update `JOURNAL.md` chronologically with decisions and outcomes.
5.  **Proactiveness**: Fix implied issues, but confirm ambiguity.

## Project Structure

```text
src/olink/
  __init__.py            # Package entry point
  core/                  # Core domain logic
    __init__.py          # Public API exports (slim: Target, REGISTRY, exceptions)
    exceptions.py        # Custom exception hierarchy
    extractors.py        # Package name extractors (pypi, npm, cargo, etc.)
    ecosystems.py        # Ecosystem config, detection, and name lookup
    git.py               # Git remote parsing & URL extraction
    targets.py           # Abstract Target & MultiEcosystemTarget base classes
    git_targets.py       # GitHub/GitLab/Bitbucket page targets
    package_targets.py   # PyPI/npm/crates/etc registry targets
    service_targets.py   # Codecov/Coveralls targets
    catalog.py           # REGISTRY dict, get_target(), list_targets()
  cli/                   # CLI interface
    __init__.py          # Exports main, app
    app.py               # Typer CLI application
  tui/                   # TUI interface
    __init__.py
    app.py               # TUI application
    models.py            # Data models
    widgets.py           # Custom widgets
    actions.py           # Action handlers
tests/
  conftest.py            # Shared fixtures
  core/                  # Core module tests
    test_utils.py
    test_platforms.py
    test_targets.py
  cli/                   # CLI tests
    test_cli.py
```
