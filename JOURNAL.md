# Development Journal

Chronological record of decisions, attempts (including failures), and outcomes. Newest entries at top.

---

## 2026-08-03 — Pinned Targets in TUI

### Context

Added a persistent pinning feature to the TUI, allowing users to mark frequently-accessed targets so they float to the top of the list across all projects.

### Decisions

- **Global pin storage**: Pins are persisted globally (not per-project) in `$XDG_CONFIG_HOME/olink/pins.json` (default `~/.config/olink/pins.json`) using stdlib `json` with no new dependencies. Matches user expectations for a machine-wide "bookmark" mechanism.
- **TUI-only feature**: Pinning is wired only in the TUI (`action_toggle_pin` in `app.py`), not in the CLI. Users toggle pins via the `p` key.
- **Visual marker**: Pinned targets are marked with `★` in the list widget to make their status obvious at a glance.
- **Pinned-first ordering**: The `order_by_pins(items, pinned)` helper in `models.py` floats pinned targets to the top, preserving their relative order, then lists the rest alphabetically (or in original order in `all` mode).
- **Graceful degradation**: Missing or corrupt pins file → empty pin set (no crash). Write failures → logged to status bar + in-memory toggle still applies (user sees the change until the next session).

### Implementation

- **`core/pins.py`**: New module with `load_pins()`, `toggle_pin()`, `save_pins()`, and helper functions for config dir/file management. Uses stdlib `json` and `pathlib`, respects `$XDG_CONFIG_HOME`.
- **`models.py`**: Added `TargetItem.pinned` boolean field and `order_by_pins(items, pinned)` helper to reorder based on the pinned set.
- **`app.py`**: Wired `load_pins()` at init, passed pinned set to `_source()`, added `action_toggle_pin()` action handler with OSError catch → status-bar error.
- **`widgets.py`**: Updated `TargetRow` to prepend `★` when `item.pinned` is True.

### Outcome

- Users can now press `p` to pin/unpin targets, with the pinned state persisting across sessions and projects.
- Pinned targets float to the top (marked with `★`) in both `available` and `all` modes.
- Failures in reading/writing pins are handled gracefully — the user sees errors in the status bar but the toggle still takes effect in-memory.
- Pins apply to the current project only when in `available` mode (unpinned targets never surface in `available` mode regardless of global pin state).

---

## 2026-07-31 — Adopt keycast-style tooling; migrate versioning to hatch-vcs

### Context

Broad tooling-migration branch that ported config and CI conventions from the sibling project [keycast](https://github.com/hasansezertasan/keycast) into olink, and replaced the release-please static-version mechanism (adopted in the 2026-06-20 entry below) with hatch-vcs.

### Decisions

- **Versioning: git tag as single source of truth (hatch-vcs)**: reversed the earlier "dropped hatch-vcs" decision. `pyproject.toml` now declares `dynamic = ["version"]` and `[tool.hatch.version] source = "vcs"`; the version is derived from the git tag and written to a generated, git-ignored `src/olink/_version.py`, re-exported as `olink.__version__`. Removed the `x-release-please-version` marker literal and the release-please `extra-files` entry that used to rewrite `pyproject.toml`. release-please now only manages `CHANGELOG.md` and the release PR, plus creates the `vX.Y.Z` tag via `force-tag-creation`. Added `fetch-depth: 0` to the publish workflow checkout so hatch-vcs can see tags when it computes the version.
- **Dev dependency pinning tightened**: dev/tool dependency groups are now exact-pinned; added `[tool.uv] add-bounds = "exact"` so future `uv add` calls default to exact pins, plus git cache-keys for reproducible resolution. Added a typos CHANGELOG-hash ignore rule, `[tool.coverage.report] exclude_also` entries, explicit pytest `testpaths`, and mypy `pretty` + `show_error_codes` for clearer local output.
- **Added `.gitattributes`** (`* text=auto eol=lf`) and a `.vscode/launch.json` for consistent line endings and one-click debugging, matching keycast.
- **Cleared pre-existing lint debt** that earlier journal entries had flagged as "unrelated to this migration": fixed the markdownlint and taplo findings across the repo (auto-fix plus targeted rule relaxation in `.config/.markdownlint.yml`), dropped taplo's `--default-schema-catalogs` flag (was causing network-dependent schema fetches), and added `[tool.ruff] extend-exclude = ["*.md"]` so ruff stops linting fenced code samples in docs.
- **CI restructured into three jobs**: `hooks` (prek, single run), `test` (pytest matrix + Codecov upload), and `typecheck` (mypy/ty matrix) — replacing a flatter single-job layout. All GitHub Actions are now SHA-pinned rather than tag-pinned, and `uv` invocations use `--frozen`/`--locked` to fail fast on lockfile drift. Added `.github/codecov.yml` to configure coverage reporting thresholds.
- **Kept poethepoet, did not switch to tox**: considered tox for the matrix runner but decided the existing `poe` task definitions were simpler to maintain for a project this size; tox would have added a second task-runner abstraction for no clear benefit.
- **Committed the design spec and implementation plan** for this migration under `docs/superpowers/` so the rationale and planned steps are preserved alongside the code, not just in PR description.
- **Left the pre-existing `GEMINI.md` deletion as-is**: that file was already deleted and unstaged going into this branch; out of scope here, so it was not touched or restored.

### Outcome

- `pyproject.toml`, CI workflows, `.config/.markdownlint.yml`, `.gitattributes`, `.vscode/launch.json`, and `docs/superpowers/` all changed; release-please config simplified to drop the version-rewrite `extra-files` entry.
- `CONTRIBUTING.md`'s release section, which still described the old release-please-rewrites-the-version mechanism, was corrected in a follow-up fix to match the hatch-vcs behavior above.

---

## 2026-07-08 — Convert config to native prek.toml

### Context

Follow-up to the pre-commit→prek runner swap below. That change intentionally left `.pre-commit-config.yaml` in place; this one completes the migration by converting to prek's native [`prek.toml`](https://prek.j178.dev/configuration/) format.

### Decisions

- **Replaced `.pre-commit-config.yaml` with `prek.toml`**: same config model (`repos` → `rev` → `hooks`), so the conversion is purely syntactic. Chose the expanded `[[repos.hooks]]` table form over inline `hooks = [{...}]` for readability now that several hooks carry `args`.
- **Used prek's `repo = "builtin"` for the `pre-commit-hooks` checks**: prek ships native Rust reimplementations of most `pre-commit/pre-commit-hooks`, so those hooks need no repo clone or `rev` and run without network setup. Moved `check-added-large-files`, `check-toml`, `check-yaml`, `check-json`, `check-merge-conflict`, `end-of-file-fixer`, and `trailing-whitespace` to `builtin`. `debug-statements` has no builtin (prek rejects it at parse time), so it stays sourced from the upstream repo. Dropped `--unsafe` from `check-yaml` — the builtin's parser is already permissive and passes all files without it.
- **Switched the `ruff` hook id to `ruff-check`**: `ruff` is now a legacy alias (prek labeled it as such), so the current id drops the warning.
- **Kept the verbose `(?x)` exclude regex** as a TOML multi-line literal string (`'''…'''`) to avoid backslash double-escaping.
- **Dropped the vanilla-pre-commit fallback**: the earlier entry kept the YAML so plain `pre-commit` still worked. That fallback is gone now — prek is the only supported runner, which matches how it's already pinned as the sole hook-runner dev dependency. (The `builtin` repo is prek-only, so this also makes the config non-portable to vanilla pre-commit by design.)

### Outcome

- `prek.toml` added, `.pre-commit-config.yaml` removed. `uv run prek validate-config prek.toml` passes; `uv run prek run --all-files` auto-discovers `prek.toml` and executes every hook with identical args.
- The taplo-lint / markdownlint / yamlfmt failures are the same pre-existing debt noted below — unaffected by the format conversion.

---

## 2026-07-08 — Migrate from pre-commit to prek

### Context

Swapped the git-hook runner from [pre-commit](https://pre-commit.com) to [prek](https://prek.j178.dev) — a drop-in Rust reimplementation that is a single dependency-free binary and runs the same hooks faster.

### Decisions

- **Kept `.pre-commit-config.yaml` unchanged**: prek is fully compatible with the existing config and hooks, so the hook definitions were left untouched rather than converting to prek's native `prek.toml`. Zero churn to the contract, and the config still works with vanilla pre-commit as a fallback.
- **Distributed as a uv dev dependency**: replaced `pre-commit>=4.0` with `prek>=0.4.8` in the `tool` dependency group (`uv remove --group tool pre-commit` + `uv add --group tool prek`), consistent with how every other dev tool is pinned via uv. Developers now run `uv run prek install` / `uv run prek run`.

### Outcome

- `pyproject.toml` + `uv.lock` are the only changed files. `pre-commit` is fully gone from the lockfile; `prek==0.4.8` resolved in.
- Verified `uv run prek run --all-files` reads the unchanged config and executes every hook. Pre-existing hook failures (taplo-lint schema-catalog fetch, markdownlint, yamlfmt drift) are untouched debt unrelated to this migration — the incidental reformatting prek produced on already-committed files was reverted to keep the change scoped.
- CI (`ci.yml`) never invoked pre-commit — it runs each linter directly via `uv run` — so no workflow changes were needed.

---

## 2026-06-20 — Switch release pipeline to release-please (follow ocom)

### Context

Adopted the release pipeline shape from the sibling project [ocom](https://github.com/hasansezertasan/ocom), replacing the release-drafter + manual-publish flow. olink had not been published to PyPI yet and had no tags, so this was effectively first-time release setup — a clean moment to swap strategies.

### Decisions

- **release-drafter → release-please**: replaced `.github/workflows/release-drafter.yml`, `.github/workflows/release.yml`, and `.github/release-drafter.yml` with a single `.github/workflows/release-please.yml` plus `release-please-config.json` and `.release-please-manifest.json`. Releases are now driven by conventional commits: release-please maintains a Release PR; merging it tags, builds, publishes to PyPI, and un-drafts the GitHub release in one automated path. No more manual "publish the draft" step.
- **Dropped hatch-vcs for ocom's static-version mechanism (`python` + `extra-files`)**: matched ocom exactly. The version is now a committed literal that release-please owns: `release-type: python` bumps `__version__` in `src/olink/__init__.py`, and `extra-files: [{ type: generic, path: pyproject.toml }]` rewrites the `version = "x.y.z" # x-release-please-version` line in `pyproject.toml`. Removed `[tool.hatch.version]`, the `hatch-vcs` build requirement, the `_version.py` file hook, and all the now-dead `_version.py` references in the mypy/pylint/vulture config. `src/olink/__init__.py` reduced to a plain `__version__ = "0.1.0"` (no more `importlib.metadata` lookup or `PackageNotFoundError` fallback).
- **No `fetch-depth: 0` needed**: with the version baked into the source, the publish checkout no longer needs git history/tags — removed it to match ocom.
- **Seeded at `0.0.0` so the first *published* release is `0.1.0`**: `pyproject.toml`, `src/olink/__init__.py`, and `.release-please-manifest.json` all start at `0.0.0`. No `bump-minor-pre-major` flag — matching [ocom PR #4](https://github.com/hasansezertasan/ocom/pull/4), which proved empirically that this release-please already bumps `feat` → minor (ocom's first Release PR proposed `0.2.0` from a `0.1.0` manifest). So `0.0.0` + a `feat` commit yields `0.1.0`. A `0.1.0` seed would have skipped straight to `0.2.0`.
- **Environment `publish`**: the publish job runs in the GitHub Environment named `publish` (matching ocom), not `pypi`.
- **Kept ocom's hardening verbatim**: pinned action SHAs and `uv publish --trusted-publishing always` (uv-native publish, no `pypa/gh-action-pypi-publish`).

### Follow-ups (manual, outside the repo)

- Configure the PyPI Trusted Publisher for `olink`: workflow `release-please.yml`, environment `pypi`.
- Ensure a GitHub Environment named `pypi` exists (protection rules optional).

---

## 2026-04-29 — Pre-PyPI release hardening

### Context

Preparing initial PyPI release. Ran a harsh review against the codebase, README, and tests. Acted on every actionable finding to make 0.1.0 publishable.

### Decisions

- **Build backend**: switched `uv_build` → `hatchling`. uv_build's narrow version range was already producing CI warnings; hatchling is the de-facto standard for `[project]`-only Python packages and is supported indefinitely.
- **Distribution shape**: kept `requires-python = ">=3.14"`. Olink is intended to be installed once per machine via `uvx` / `pipx tool install`, not pinned per-project, so the latest-Python floor doesn't hurt adoption the way it would for a library.
- **TUI deps**: moved `textual` and `pyperclip` to `[project.optional-dependencies] tui`. CLI users no longer pay for ~15 MB of TUI dependencies. CLI gracefully reports the missing extra with the exact install hint.
- **Codecov/Coveralls on Gitea/Forgejo**: chose to raise `UnsupportedFeatureError` rather than emit silently-broken URLs. Better to fail loudly when the upstream service has no integration than to send users to 404s.
- **Hostname platform detection**: switched substring (`"gitlab" in host`) to label-based (`split(".")` then exact match). Substring matched `gitlabby.example.com` and friends; label match doesn't.
- **CPAN ecosystem detection**: extended `EcosystemConfig` with `extra_signals` so detection accepts `Makefile.PL` OR `dist.ini` OR `lib/*.pm`. Resolves the long-standing divergence where `olink cpan` worked direct but never appeared in `--list` for `dist.ini`-only or `lib/`-only Perl projects.
- **Open VSX**: registered as its own ecosystem (`open-vsx` → `package.json` + publisher field). Now autodetected and listed in `--list` for VS Code extension projects.
- **PyPI publishing**: chose OIDC trusted publishing over API tokens. No secrets in repo, automatic short-lived credentials, scoped to the specific `release.yml` workflow + `pypi` environment.
- **Release pipeline (drafter + hatch-vcs)**: `release-drafter.yml` runs on push-to-main and PR events, accumulating PR titles + autolabels into a single Draft GitHub Release. The maintainer publishes the draft when ready, which creates tag `vX.Y.Z`. The tag fires `release.yml` (build via `uv build` → `hatch-vcs` reads the tag → `pypa/gh-action-pypi-publish@release/v1` via OIDC → upload artifacts). The GitHub Releases page is the single source of truth for the changelog; no in-repo `CHANGELOG.md` is maintained.
- **PR-title linting**: `amannn/action-semantic-pull-request` enforces Conventional Commits on PR titles so release-drafter's autolabeler classifies changes correctly (feat → minor, fix → patch, breaking → major) and the release notes read cleanly.
- **Type checking**: added `[tool.mypy]` strict config and `py.typed` PEP 561 marker. Honours the `Typing :: Typed` classifier the package already advertises.

### Changes

**Bugs fixed**

- `CodecovTarget` / `CoverallsTarget`: raise `UnsupportedFeatureError` for non-supported platforms instead of building 404 URLs.
- `parse_remote_url`: hostname-label matching prevents false-positive platform detection on substrings.
- `_collect_insteadof_rewrites`: strips trailing `# comment` / `; comment` from values.
- `get_remote_url`: reads `.git/config` once per call (was twice).
- `EcosystemConfig.exists`: `sorted()` glob results for deterministic detection across filesystems.
- CPAN `lib/` walk: stable tiebreaker `(len(parts), as_posix())` for siblings.

**Metadata / packaging**

- `pyproject.toml`: full PyPI metadata — `license = "MIT"`, `LICENSE` file, `authors`, `keywords`, `classifiers`, `[project.urls]`, `description` from README first line.
- `[project.optional-dependencies] tui = [textual, pyperclip]`.
- `[tool.ruff]` (line-length 100, py314, E/F/I/B/UP/ANN/RUF rules).
- `[tool.mypy]` (strict, Python 3.14, files = `src/olink`).
- `LICENSE`, `src/olink/py.typed` created.
- `.gitkeep` removed.

**CLI**

- `__version__` exported via `importlib.metadata.version("olink")`.
- `--version` / `-V` flag (eager callback).
- TUI launch wrapped in `try/except ImportError` with actionable install hint.
- `B904` fixed: `raise typer.Exit(1) from e`.

**Tests**

- 257 → 286 (+29 net).
- New: `--version`/`-V` flag, codecov/coveralls gitea/forgejo unsupported, `ssh://` port form refusal, hostname false-positive guard, insteadOf trailing-comment strip, scoped npm-stat/packagephobia URL encoding, registry-drift guard, CPAN multi-signal detection.
- `TestRegistryURLCoverage`: 16 missing-target URL assertions (inspector, pypi-json, pepy, pypistats, piptrends, clickpy, safety-db, bundlephobia, packagephobia, npm-stat, librs, packagist, pub, hex, nuget, …).
- Renamed `tests/core/test_utils.py` → `test_project.py` (matched the actual module under test).
- `os.geteuid()` skip-marker now win32-safe via `getattr`.
- `caplog.set_level` moved before triggering action.
- `conftest.copy_repo_fixture` now `shutil.copytree(..., dirs_exist_ok=True)` — subdir-safe.

**CI / CD**

- `.github/workflows/ci.yml`: pytest matrix (ubuntu+macos, py3.14), ruff check + format, mypy job.
- `.github/workflows/release-drafter.yml` + `.github/release-drafter.yml`: maintains a Draft GitHub Release by accumulating PR titles + autolabels; resolves version from `major`/`minor`/`patch` labels.
- `.github/workflows/release.yml`: three-job pipeline (build → pypi-publish → attach-github-release) triggered on `release: published`. Uses `pypa/gh-action-pypi-publish@release/v1` with OIDC; environment `pypi`. Build version comes from the git tag via `hatch-vcs`.
- `.github/workflows/check-pr-title.yml`: enforces Conventional Commits on PR titles.
- `pyproject.toml`: `dynamic = ["version"]`, `[tool.hatch.version] source = "vcs"` with `fallback-version = "0.1.0"` and `local_scheme = "no-local-version"`; `_version.py` written to `src/olink/` at build time and gitignored.

**Docs**

- README: `[tui]` install hint, `--version` line, CPAN multi-signal note.

### Outcome

- 286/286 tests pass.
- ruff clean.
- mypy strict clean (13 source files).
- Trusted publishing wired and tagged-release-driven.

### Release ritual (going forward)

- Land any number of Conventional-Commit PRs onto `main`. Autolabeler tags each PR (`enhancement`, `bug`, `dependencies`, …).
- `release-drafter` keeps a single Draft GitHub Release in sync, with the next version resolved from the strongest label (major > minor > patch).
- When ready to ship, edit the draft if needed and click **Publish**. That creates tag `vX.Y.Z` and the GitHub Release.
- `release.yml` fires on `release: published`: `uv build` (hatch-vcs reads the tag) → `pypa/gh-action-pypi-publish@release/v1` via OIDC → attach dist files to the release.
- The GitHub Releases page is the only changelog. No in-repo `CHANGELOG.md`.
- No tag is ever pushed by hand. `pyproject.toml` carries `dynamic = ["version"]`; the version lives in the git tag.

---

## 2026-04-29 — Codebase audit: bug fixes, new features, expanded test coverage

### Context

Audit of README/code/docstring/test consistency. Found bugs (CPAN heuristic, Maven parent), missing features (Gitea/Forgejo, `insteadOf`), and test gaps (TUI rendering, edge cases). Worked through all in one pass.

### Changes

**Bugs fixed**

- CPAN: reordered fallback chain (Makefile.PL → lib/ → dist.ini). lib/ layout is more reliable than the dist.ini hyphen-to-colon heuristic which fails on names like `Foo-Bar` distributions whose actual module is `FooBar`.
- Maven: parent groupId lookup now walks the full `<parent>` chain via `<relativePath>` (defaults to `../pom.xml`). Bounded at 8 levels. Earlier one-level lookup missed corporate parent → product parent → service artifact patterns.
- GitLab subgroup warning was misleading — generated URLs are correct. Downgraded to `debug`.

**Features added**

- Gitea / Forgejo / Codeberg platform support. Hostname heuristic + GitHub-compatible PLATFORM_URLS entries.
- `[url].insteadOf` rewrite support. Longest-prefix match wins, matching git's algorithm. Lets shorthand remotes like `github:owner/repo` resolve correctly.

**Hardening**

- Centralized `_read_text(path, label)` helper wraps `PermissionError` and `UnicodeDecodeError` to `ProjectMetadataError` across all 12 extractors. Same wrapping in `_read_git_config` for consistent CLI errors.
- Added docstrings (contract, raises, edge cases) to all `_get_*_name()` functions and most Target subclasses, satisfying the project's "Required for public interfaces" rule.

**Test coverage**

- 211 → 244 tests.
- Added: Maven grandparent + no-group-in-chain, CPAN lib-wins-over-dist.ini, empty config files (5), invalid TOML, invalid UTF-8, permission-denied (POSIX-only), symlinked dir, Gitea/Forgejo/Codeberg targets, `insteadOf` rewrite (3 cases incl. longest-match), TUI render via Pilot (StatusBar, TargetListWidget, search flow, toggle mode, action handlers).
- Added `pytest-asyncio` (auto mode) for Textual `App.run_test()` Pilot tests.

### Lesson learned

**Tests caught a real bug in the fix.** The first Maven recursive-walk implementation only inspected `<parent>` child's `groupId`, never the **top-level** `groupId` of the next parent pom. The grandparent test failed immediately and forced the second `findtext` after each pom switch. Without that test, the bug would have shipped silently.

**Centralize before the third copy.** The first two extractors got hand-rolled `try/except PermissionError`. Twelve became unworkable — pulled out `_read_text(path, label)` once and reused everywhere. Repeated boilerplate is a smell that points at the missing abstraction.

---

## 2026-02-22: Review Follow-up for Expanded Targets

### Context

Follow-up review requested additional hardening and edge-case coverage on the expanded target set.

### The Change

- Improved CPAN package detection to prefer `dist.ini` project metadata before falling back to `cpanfile` dependency parsing.
- Added a `dist.ini` fixture for Perl projects so CPAN target tests assert distribution-level behavior.
- Expanded negative-path tests for new targets (`go-docs`, `rubygems-stats`, `jsdelivr`, `unpkg`, `skypack`, `open-vsx`, `maven`, `hackage`, `cpan`) to lock in user-facing error messages when required metadata is missing.

### Outcome

New targets now have stronger error-path coverage and CPAN links are more likely to point to the actual distribution under development.

---

## 2026-02-22: Implemented Full Target Expansion Set

### Context

Follow-up requested implementing the full brainstormed target set rather than keeping it as notes.

### The Change

- Added 10 targets across existing and new ecosystems:
  - `rubygems-stats`, `go-docs`, `jsdelivr`, `unpkg`, `skypack`, `socket`, `open-vsx`, `maven`, `hackage`, `cpan`.
- Extended ecosystem extraction to support Open VSX (`package.json` publisher+name), Maven (`pom.xml`), Hackage (`*.cabal`), and CPAN (`cpanfile`).
- Added fixtures and tests covering URL generation and target registry membership for all new targets.
- Updated README tables/examples so new targets are discoverable from docs.

### Outcome

The previously proposed target shortlist is now implemented with test coverage and surfaced in user-facing documentation.

---

## 2026-02-22: Target Expansion Brainstorm (Web Search Blocked)

### Context

A request came in for a quick scan of additional `olink` targets to add next.

### The Attempt

- Tried to run a lightweight web search via `curl` against DuckDuckGo.
- The environment returned `CONNECT tunnel failed, response 403`, so live search results were unavailable from this container.

### Proposed Targets

Based on ecosystem fit with the current target model (registry pages, docs pages, and package analytics), these are strong candidates:

1. **RubyGems stats**: `rubygems-stats` → `https://rubygems.org/gems/<name>/stats`
2. **pkg.go.dev docs**: `go-docs` → `https://pkg.go.dev/<module>`
3. **jsDelivr package view**: `jsdelivr` → `https://www.jsdelivr.com/package/npm/<name>`
4. **UNPKG package view**: `unpkg` → `https://unpkg.com/<name>`
5. **Skypack package view**: `skypack` → `https://www.skypack.dev/view/<name>`
6. **Socket.dev package health**: `socket` (multi-ecosystem) with ecosystem-specific paths
7. **Open VSX extension page**: `open-vsx` for VS Code extension projects
8. **Maven Central artifact page**: `maven` for Java/Kotlin projects (`groupId:artifactId`)
9. **Hackage package page**: `hackage` for Haskell projects
10. **CPAN package page**: `cpan` for Perl projects

### Outcome

Recorded a concrete shortlist that can be implemented without changing the architecture, while noting that network-enabled validation of market demand should be done outside this restricted environment.

---

## 2026-02-22: New target expansion for Rust + Go discovery

### Decision

Add dedicated `docsrs` and `pkg-go` targets so users can open the most common language-specific documentation hubs directly.

### Why

The existing target set already supports Rust and Go package discovery via registry and multi-ecosystem services, but docs-focused entry points were missing. Adding these two targets keeps the CLI useful for the "I need API docs now" workflow without adding complexity.

### Outcome

- Added `docsrs` target (`https://docs.rs/<crate>`).
- Added `pkg-go` target (`https://pkg.go.dev/<module>`).
- Updated registry, tests, and README target tables.

---

## 2026-02-12: Follow-up on piwheels Test Coverage and Formatting

### Context

Review feedback requested explicit CLI error-path coverage for `piwheels` without `pyproject.toml`, plus a small readability cleanup in target tests.

### The Change

- Added a CLI dry-run error test for `piwheels` that asserts the expected missing `pyproject.toml` message.
- Inserted a blank line between piwheels target tests for consistent spacing and readability.
- Verified `REGISTRY` remains explicitly imported where `len(REGISTRY)` is asserted.

### Outcome

The piwheels feature now has both success and failure behavior covered through the CLI surface, and the related tests are formatted consistently.

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

1. **User Errors vs. Bugs**:
    In `cli.py`, we catch `OlinkError` to display clean error messages (exit code 1) while letting generic exceptions crash with a stack trace. This ensures programming bugs aren't accidentally swallowed as "user errors".

2. **Test Precision**:
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

```text
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
3. **URL rewrites**: `[url "..."].insteadOf` directives (NOT supported — added 2026-04-29)
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
