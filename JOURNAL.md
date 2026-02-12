# Development Journal

Chronological record of decisions, attempts (including failures), and outcomes.

---

## 2026-02-12: Follow-up on piwheels Review Feedback

### Context

Review feedback flagged a brittle target-count assertion and suggested tighter docstrings for new piwheels-related additions.

### The Change

- Updated `test_list_targets_returns_all` to assert against `len(REGISTRY)` instead of a hard-coded number.
- Shortened piwheels class and test docstrings to keep intent clear and scannable.

### Outcome

Future target additions no longer require changing a magic count in tests, and piwheels documentation reads more consistently with the rest of the codebase.

---

## 2026-02-12: Added piwheels Target Support

### Context

Python projects in this tool already supported PyPI and related analytics targets, but lacked a direct shortcut to piwheels for Raspberry Pi package builds.

### The Change

- Added a dedicated `piwheels` target that reuses PyPI package-name detection from `pyproject.toml`.
- Registered the target in the central catalog so it appears in discovery and CLI lookup flows.
- Expanded tests and README documentation to make the new target discoverable and verified.

### Outcome

`olink piwheels` now opens `https://www.piwheels.org/project/<package>/` for Python projects while preserving existing metadata error behavior.

---

## 2026-02-01: Decision to Keep Custom Exceptions

### Context

The project defines a custom exception hierarchy in `src/olink/exceptions.py` (`OlinkError` > `NotGitRepoError`, etc.). We evaluated whether to replace these with standard Python exceptions (`ValueError`, `RuntimeError`) to reduce boilerplate.

### The Decision

**Keep the custom exceptions.**

### Rationale

1.  **User Errors vs. Bugs**:
    In `cli.py`, we catch `OlinkError` to display clean error messages (exit code 1) while letting generic exceptions crash with a stack trace. This ensures programming bugs aren't accidentally swallowed as "user errors".

2.  **Test Precision**:
    Tests can verify exact failure modes. `pytest.raises(NoRemoteError)` ensures the test passes only for the expected logic path, whereas `pytest.raises(Exception)` might mask unrelated bugs (e.g., a `KeyError` or `AttributeError`).

### Outcome

Retained `src/olink/exceptions.py` and the `try...except OlinkError` pattern in the CLI.

---

## 2026-02-01: Refactored Registry Targets

### Context

Detected code duplication between `src/olink/targets/registry_targets.py` and `src/olink/ecosystems.py`. Both implemented identical logic for parsing `pyproject.toml`, `package.json`, and `Cargo.toml`.

### The Change

Refactored `registry_targets.py` to remove local helper functions and use the centralized `get_package_name` from `ecosystems.py`.

### Result

- Reduced code duplication (DRY).
- Centralized parsing logic in `ecosystems.py`.
- Verified with existing test suite.

---

## 2026-02-01: Replaced Platform Classes with Data Dict

### Context

The `platforms/` directory contained 5 files with classes for GitHub, GitLab, and Bitbucket URL generation:

```
platforms/
├── __init__.py    # Registry + imports
├── base.py        # Abstract Platform class
├── github.py      # GitHubPlatform class
├── gitlab.py      # GitLabPlatform class
└── bitbucket.py   # BitbucketPlatform class
```

Each platform class had 3 methods that did nothing but string concatenation:

```python
class GitHubPlatform(Platform):
    def issues_url(self, parsed: ParsedRemote) -> str:
        return f"{parsed.base_url}/issues"

    def pulls_url(self, parsed: ParsedRemote) -> str:
        return f"{parsed.base_url}/pulls"

    def actions_url(self, parsed: ParsedRemote) -> str:
        return f"{parsed.base_url}/actions"
```

### The Problem

This was **over-engineering**. The platform classes:

- Had no real behavior to encapsulate
- Only concatenated strings with URL path suffixes
- Required 5 files and ~100 lines for what is essentially configuration data
- Added unnecessary abstraction (abstract base class, registry pattern)

### The Insight

> When code only transforms data without complex logic, represent it as **data** (dicts, lists) rather than classes. Classes add indirection without benefit when there's no behavior to encapsulate.

### The Solution

Replaced the entire `platforms/` directory with a single dict in `git_targets.py`:

```python
PLATFORM_URLS = {
    "github": {"issues": "/issues", "pulls": "/pulls", "actions": "/actions"},
    "gitlab": {"issues": "/-/issues", "pulls": "/-/merge_requests", "actions": "/-/pipelines"},
    "bitbucket": {"issues": "/issues", "pulls": "/pull-requests", "actions": "/pipelines"},
}

def get_platform_url(base_url: str, platform: str, page: str) -> str:
    """Get URL for a specific page on a platform."""
    if platform not in PLATFORM_URLS:
        raise UnknownPlatformError(f"Unknown platform: '{platform}'")
    return base_url + PLATFORM_URLS[platform][page]
```

### Benefits

| Aspect            | Before                             | After                        |
| ----------------- | ---------------------------------- | ---------------------------- |
| Files             | 5                                  | 0 (inline in git_targets.py) |
| Lines of code     | ~100                               | ~10                          |
| To add a platform | Create new file + class + register | Add 1 line to dict           |
| Readability       | Scattered across files             | All data visible at a glance |
| Testability       | Mock classes                       | Assert dict values           |

### Why I Initially Hesitated

When asked "Does it make sense to have a platforms/ directory?", I presented three options:

- **Option A:** Consolidate into single `platforms.py`
- **Option B:** Move into `core/`
- **Option C:** Inline as a dict in `git_targets.py`

I recommended A or B, not C. When challenged with "What is wrong with option C?", I realized I was being **conservative** — reaching for classes and separate files out of habit, not necessity.

**Why the hesitation?**

1. **Familiarity bias** — Classes feel "proper" for representing entities like platforms
2. **Premature abstraction** — Thinking "what if we need complex logic later?" (we don't)
3. **Industry patterns** — Seeing class hierarchies in other projects and assuming they're always appropriate
4. **Fear of "too simple"** — A dict felt too basic to be the "right" answer

**The reality:** The simplest solution was the best solution. The user's pushback ("Why don't you recommend Option C?") forced me to honestly evaluate why I was avoiding it — and I had no good reason.

### Lesson Learned

**Ask: "Is this code, or is this data?"**

If the "logic" is just mapping inputs to outputs with no conditionals, loops, or state — it's data. Use a dict.

**Also:** When you hesitate to recommend the simplest solution, ask yourself why. If the answer is "it feels too simple" or "what if we need more later" — that's not a reason. Simplicity is a feature, not a flaw.

---

## 2026-02-01: Replaced Subprocess Calls with File-Based Git Operations

### Context

The `core/git.py` module used `subprocess.run()` to call git commands:

```python
# is_git_repo
subprocess.run(["git", "rev-parse", "--git-dir"], ...)

# get_remote_url
subprocess.run(["git", "remote", "get-url", remote_name], ...)

# get_remote_names (unused, later deleted)
subprocess.run(["git", "remote"], ...)
```

### The Question

> "Can't we replace subprocess calls with reading `.git/config` directly?"

### Trade-offs Analysis

| Aspect       | Subprocess (`git` commands) | File-based (`.git/config`) |
| ------------ | --------------------------- | -------------------------- |
| Speed        | ~10-50ms per call           | <1ms                       |
| Dependencies | Requires `git` installed    | None                       |
| Edge cases   | Handled by git              | Must handle ourselves      |
| Maintenance  | Git handles internals       | We own the parser          |

### Edge Cases to Handle

1. **Worktrees**: `.git` is a file containing `gitdir: /path/to/main/.git/worktrees/branch`
2. **Submodules**: `.git` is a file containing `gitdir: ../.git/modules/submodule`
3. **URL rewrites**: `[url "..."].insteadOf` directives (NOT supported)
4. **Config includes**: `[include]` directives (NOT supported)

### The Solution

Read `.git/config` directly using Python's `configparser`:

```python
def _get_git_dir(cwd: str) -> Path | None:
    """Get the .git directory path, handling worktrees and submodules."""
    git_path = Path(cwd) / ".git"

    if git_path.is_dir():
        return git_path  # Regular repo

    if git_path.is_file():
        # Worktree or submodule: parse gitdir reference
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            gitdir = content[7:].strip()
            return Path(gitdir) if Path(gitdir).is_absolute() else (Path(cwd) / gitdir).resolve()

    return None

def _read_git_config(cwd: str) -> configparser.ConfigParser:
    """Read and parse .git/config file."""
    git_dir = _get_git_dir(cwd)
    config = configparser.ConfigParser()
    config.read(git_dir / "config")
    return config
```

### Documented Limitations

Added to module docstring:

```python
"""Git operations and URL parsing.

Note: This module reads .git/config directly instead of calling git commands.
This is faster but has limitations:
- Does not support [url "..."].insteadOf rewrites
- Does not support [include] directives in git config
"""
```

### Also: Deleted Unused Code

While refactoring, discovered `get_remote_names()` was never used outside tests. Deleted it — no point maintaining code that isn't used.

### Benefits

| Aspect        | Before                      | After                                 |
| ------------- | --------------------------- | ------------------------------------- |
| Speed         | ~50ms (subprocess overhead) | <1ms (file read)                      |
| Dependencies  | Requires `git` binary       | None (stdlib only)                    |
| Lines of code | 30                          | 35 (but handles worktrees/submodules) |

### Lesson Learned

**File I/O is faster than subprocess.** When you only need to read configuration data that's stored in a well-defined format, reading the file directly is simpler and faster than spawning a subprocess. The trade-off is you need to handle edge cases yourself — but for a focused tool like `olink`, the 95% case (regular repos with standard config) is sufficient.

**Document your limitations.** Rather than pretend the file-based approach is equivalent to `git`, document what it doesn't support (`insteadOf`, `include`). Users who rely on those features will know why it doesn't work.
