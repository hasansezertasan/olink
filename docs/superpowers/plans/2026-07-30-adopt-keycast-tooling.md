# Adopt keycast tooling & configuration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adopt keycast's tooling/config into olink — migrate to hatch-vcs git-tag versioning (removing `x-release-please-version`), pin dev deps exactly, harden CI (SHA-pinned actions, `--frozen`, prek-consolidated lint, Codecov), and add small config niceties.

**Architecture:** Pure config/tooling change. The version literal in `pyproject.toml` is
replaced by `dynamic = ["version"]` fed by hatch-vcs from the git tag; release-please stops
editing `pyproject.toml` and instead force-creates the tag. CI is restructured into three
jobs (`hooks` = prek, `test` = matrix + coverage, `typecheck` = matrix). Task runner stays
poethepoet.

**Tech Stack:** Python 3.14, uv, hatchling + hatch-vcs, poethepoet, prek, ruff, pytest +
coverage, release-please, GitHub Actions, Codecov.

## Global Constraints

- Python floor: `requires-python = ">=3.14"`; all tool configs target `py314` / `3.14`.
- Task runner is **poethepoet** — do NOT introduce tox.
- `prek.toml` keeps its builtin-native-hook style — do NOT downgrade to upstream-repo style.
- Only **dev-dependency groups** (`lint`/`test`/`tool`) are pinned to exact `==`. Runtime
  and optional (`[tui]`) deps keep their existing specifiers.
- Every GitHub Actions `uses:` is pinned to a full commit SHA with a `# vX.Y.Z` comment.
- No commit contains any AI-authorship trailer/footer; Conventional Commits for messages.
- Design spec: `docs/superpowers/specs/2026-07-30-adopt-keycast-tooling-design.md`.

**Resolved action SHAs (use verbatim):**

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
- `astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9 # v9.0.0`
- `codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0`
- `amannn/action-semantic-pull-request@48f256284bd46cdaab1048c3721360e808335d50 # v6.1.1`
- `marocchino/sticky-pull-request-comment@5770ad5eb8f42dd2c4f34da00c94c5381e49af88 # v3.0.5`

**Resolved dev-dep pins (from uv.lock):**
`mypy==2.3.0`, `pyright==1.1.411`, `ty==0.0.65`, `pyrefly==1.1.1`, `pylint==4.0.6`,
`ruff==0.16.0`, `taplo==0.9.3`, `typos==1.48.0`, `validate-pyproject[all]==0.25`,
`vulture==2.16`, `slotscheck==0.20.1`, `pytest==9.1.1`, `pytest-asyncio==1.4.0`,
`pytest-cov==7.1.0`, `pytest-mock==3.15.1`, `pytest-xdist==3.8.0`, `coverage[toml]==7.15.2`,
`coverage-enable-subprocess==1.0`, `poethepoet==0.48.0`, `prek==0.4.11`.
Build deps (not in lock, pin to keycast's known-good): `hatchling==1.31.0`, `hatch-vcs==0.5.0`.

---

## Task 1: hatch-vcs versioning migration

**Files:**

- Modify: `pyproject.toml` (`[project]`, `[build-system]`, add `[tool.hatch.*]`)
- Modify: `src/olink/__init__.py:3-5`
- Modify: `.github/release-please-config.json`
- Modify: `.github/workflows/release-please.yml` (publish job checkout)
- Modify: `tests/cli/test_cli.py` (docstring of `test_version_renders_package_version`)

**Interfaces:**

- Produces: `src/olink/_version.py` (generated at build/sync; already gitignored) exposing
  `__version__: str`. `olink.__version__` re-exports it; `olink/cli/app.py:8` already
  imports `from olink import __version__` — no change needed there.

- [ ] **Step 1: Replace the static version with `dynamic`**

In `pyproject.toml` `[project]`, change:

```toml
version = "0.1.0" # x-release-please-version
```

to:

```toml
dynamic = ["version"]
```

- [ ] **Step 2: Pin build backend and add hatch-vcs**

In `pyproject.toml`, replace `[build-system]`:

```toml
[build-system]
requires = ["hatchling==1.31.0", "hatch-vcs==0.5.0"]
build-backend = "hatchling.build"
```

- [ ] **Step 3: Add hatch version config**

Add to `pyproject.toml` (near the existing `[tool.hatch.build.targets.*]` blocks):

```toml
[tool.hatch.version]
# Single source of truth is the git tag. On a release tag this resolves to the exact
# X.Y.Z; with no tag it falls back to fallback-version below.
source = "vcs"
fallback-version = "0.0.0"

[tool.hatch.version.raw-options]
# Use the tag exactly (don't guess the next release) and drop the PEP 440 local
# segment (+g<hash>) so non-tag builds stay PyPI-uploadable.
version_scheme = "only-version"
local_scheme = "no-local-version"

[tool.hatch.build.hooks.vcs]
# Write the computed version to a generated, git-ignored module.
version-file = "src/olink/_version.py"
```

- [ ] **Step 4: Re-export `__version__` from the generated module**

Replace `src/olink/__init__.py` body:

```python
"""olink - Open external URLs related to your project."""

from olink._version import __version__

__all__ = ["__version__"]
```

- [ ] **Step 5: Stop release-please editing pyproject, force-create the tag**

Replace `.github/release-please-config.json` `packages["."]` block so it reads:

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "packages": {
    ".": {
      "release-type": "python",
      "draft": true,
      "force-tag-creation": true,
      "include-component-in-tag": false,
      "bump-minor-pre-major": true
    }
  }
}
```

(The `extra-files` block is removed; `force-tag-creation` makes the tag exist at build
time for hatch-vcs; `bump-minor-pre-major` keeps pre-1.0 breaking changes on minor.)

- [ ] **Step 6: Give the publish build full history**

In `.github/workflows/release-please.yml`, the `publish` job's checkout step currently is:

```yaml
      - name: Checkout repository
        uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
```

Add `with: fetch-depth: 0` (hatch-vcs needs the tag/history to compute the version):

```yaml
      - name: Checkout repository
        uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0
        with:
          # hatch-vcs derives the version from the release tag, so uv build needs full history.
          fetch-depth: 0
```

- [ ] **Step 7: Fix the now-stale test docstring**

In `tests/cli/test_cli.py`, `test_version_renders_package_version`, replace the docstring
sentence that says release-please owns `__version__` as a static literal with:

```python
        """`--version` must echo exactly the `__version__` it imported.

        `__version__` now comes from the git tag via hatch-vcs (generated
        `olink/_version.py`), so this pins the wiring, not a literal: monkeypatch the
        symbol the CLI module imported and assert the flag prints it verbatim.
        """
```

Leave the test body (the `monkeypatch.setattr(cli_module, "__version__", "9.9.9")` and the
assertion) unchanged.

- [ ] **Step 8: Regenerate the environment and verify end-to-end**

Run:

```bash
uv sync --all-extras
test -f src/olink/_version.py && echo "_version.py generated"
uv run olink --version
uv run pytest "tests/cli/test_cli.py::TestCLIHelp::test_version_renders_package_version" -v || uv run pytest -k version -v
uv build --no-sources --quiet && ls dist/
grep -rn "x-release-please-version" . --exclude-dir=.git --exclude-dir=docs && echo "STILL PRESENT (bad)" || echo "marker gone (good)"
```

Expected: `_version.py generated`; `olink --version` prints a version (tag-derived, or
`0.0.0` on a tagless checkout); version test PASSES; `dist/` holds a wheel + sdist; the
grep prints "marker gone (good)".

> Note: `test_version_renders_package_version` lives in class `TestCLIHelp` in
> `tests/cli/test_cli.py`; the `|| uv run pytest -k version -v` fallback covers a rename.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml src/olink/__init__.py .github/release-please-config.json \
        .github/workflows/release-please.yml tests/cli/test_cli.py uv.lock
git commit -m "build: derive version from git tags via hatch-vcs

Drop the static version literal and x-release-please-version marker; release-please now
force-creates the tag that hatch-vcs reads at build time."
```

---

## Task 2: pyproject config modernization

**Files:**

- Modify: `pyproject.toml` (`[tool.uv]`, dependency groups, `[tool.typos]`,
  `[tool.coverage.report]`, `[tool.pytest.ini_options]`, `[tool.mypy]`)

**Interfaces:**

- Consumes: nothing from Task 1 beyond a working `pyproject.toml`.
- Produces: no code symbols; a stricter, pinned dev environment.

- [ ] **Step 1: Exact uv bounds + git cache-keys**

Replace `[tool.uv]`:

```toml
[tool.uv]
add-bounds = "exact"
cache-keys = [
  { file = "pyproject.toml" },
  { git = { commit = true, tags = true } },
]
trusted-publishing = "always"
```

- [ ] **Step 2: Pin dev dependency groups exactly**

Replace the `lint`, `test`, and `tool` groups in `[dependency-groups]` with (keep the
`dev` group and its `include-group` entries as-is):

```toml
lint = [
  "mypy==2.3.0",
  "pyright==1.1.411",
  "ty==0.0.65",
  "pyrefly==1.1.1",
  "pylint==4.0.6",
  "ruff==0.16.0",
  "taplo==0.9.3",
  "typos==1.48.0",
  "validate-pyproject[all]==0.25",
  "vulture==2.16",
  "slotscheck==0.20.1",
]
test = [
  "pytest==9.1.1",
  "pytest-asyncio==1.4.0",
  "pytest-cov==7.1.0",
  "pytest-mock==3.15.1",
  "pytest-xdist==3.8.0",
  "coverage[toml]==7.15.2",
  "coverage-enable-subprocess==1.0",
]
tool = ["poethepoet==0.48.0", "prek==0.4.11"]
```

- [ ] **Step 3: Add typos CHANGELOG-hash ignore**

Add to `pyproject.toml`:

```toml
[tool.typos.default]
# release-please writes commit links like `[9ae107a]` into CHANGELOG.md; the abbreviated
# SHA can read as a word fragment. Ignore the bracketed hash token wholesale ({7,40}
# covers git extending the abbreviation up to the full 40-char hash).
extend-ignore-re = ["\\[[0-9a-f]{7,40}\\]"]
```

- [ ] **Step 4: Modernize coverage excludes**

In `[tool.coverage.report]`, rename `exclude_lines` to `exclude_also` and add the
ellipsis-body pattern, so it reads:

```toml
[tool.coverage.report]
show_missing = true
skip_covered = true
exclude_also = [
  "no cov",
  "if __name__ == .__main__.:",
  "if TYPE_CHECKING:",
  "raise NotImplementedError",
  "\\.\\.\\.",
]
```

- [ ] **Step 5: pytest testpaths + mypy output niceties**

In `[tool.pytest.ini_options]` add:

```toml
testpaths = ["tests"]
```

In `[tool.mypy]` add:

```toml
pretty = true
show_error_codes = true
```

- [ ] **Step 6: Relock and verify the toolchain still passes**

Run:

```bash
uv lock
uv sync --all-extras
uv run validate-pyproject pyproject.toml
uv run poe style
uv run poe typecheck
uv run poe test
```

Expected: `uv lock` succeeds; validate-pyproject reports valid; `poe style`, `poe
typecheck`, and `poe test` all pass.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: pin dev deps exactly and modernize tool config

Add uv add-bounds=exact + git cache-keys, pin lint/test/tool groups, ignore CHANGELOG
commit-hash tokens in typos, switch coverage to exclude_also, set pytest testpaths and
mypy pretty output."
```

---

## Task 3: root config files (.gitattributes, .vscode)

**Files:**

- Create: `.gitattributes`
- Create: `.vscode/launch.json`

**Interfaces:**

- Consumes/Produces: none (editor + git-attribute config only).

- [ ] **Step 1: Add `.gitattributes`**

Create `.gitattributes`:

```
* text=auto eol=lf
```

- [ ] **Step 2: Renormalize line endings and confirm no surprise churn**

Run:

```bash
git add --renormalize .
git status --porcelain
git diff --cached --stat
```

Expected: on a Unix-developed repo this is a no-op or a tiny normalization. If large
unexpected reformatting appears, STOP and report before committing.

- [ ] **Step 3: Add a VS Code debug config**

Create `.vscode/launch.json`:

```json
{
    // Launch the olink CLI under the debugger via uv. The prompt supplies args
    // (default `--version`); e.g. enter `pypi` or `--help` to debug other paths.
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: olink",
            "type": "debugpy",
            "request": "launch",
            "justMyCode": true,
            "module": "uv",
            "args": [
                "run",
                "olink",
                "${input:args}"
            ]
        }
    ],
    "inputs": [
        {
            "id": "args",
            "type": "promptString",
            "default": "--version",
            "description": "Arguments passed to olink"
        }
    ]
}
```

- [ ] **Step 4: Verify hooks accept the new files**

Run:

```bash
uv run prek run --all-files --show-diff-on-failure
```

Expected: PASS (note `prek.toml` excludes `.vscode/launch.json` from `check-json` via the
existing config on keycast; olink's `check-json` builtin has no such exclude, and
`launch.json` contains `//` comments — if `check-json` fails on it, add
`exclude = '^\.vscode/launch\.json$'` to olink's `check-json` builtin hook args in
`prek.toml`, then re-run).

- [ ] **Step 5: Commit**

```bash
git add .gitattributes .vscode/launch.json
# include any files renormalized in Step 2, and prek.toml if edited in Step 4:
git add -A
git commit -m "chore: add .gitattributes (eol=lf) and VS Code debug config"
```

---

## Task 4: Green the prek suite & commit project docs

**Goal:** Make BOTH `uv run prek run --all-files` AND `uv run poe style` exit 0, and commit
the project's design spec + implementation plan (`docs/superpowers/**`). This clears
pre-existing lint debt that olink's old CI never enforced but the new prek-based CI (Task 5)
will. Added mid-execution per user decision "fix the debt now".

**Files:**

- Modify: `prek.toml` (taplo-lint hook — drop `--default-schema-catalogs`)
- Modify: `pyproject.toml` (`[tool.ruff]` — stop ruff formatting Markdown)
- Modify: `.config/.markdownlint.yml` (relax rules that fight narrative/template docs; ignore internal docs)
- Modify (auto-fix): `README.md`, `AGENTS.md`, `CHANGELOG.md`, `JOURNAL.md`, and the
  `.github/**/*.md` templates as needed to satisfy markdownlint
- Add: `docs/superpowers/specs/2026-07-30-adopt-keycast-tooling-design.md`,
  `docs/superpowers/plans/2026-07-30-adopt-keycast-tooling.md` (commit the untracked `docs/`)

**Interfaces:**

- Consumes: Tasks 1–3 (working tree state).
- Produces: a repo where `prek run --all-files` and `poe style` both pass (Task 5 CI + Task
  6 verification depend on this).

**Constraints / policy:**

- `GEMINI.md` is deleted in the working tree (not ours). Do NOT restore it and do NOT stage
  its deletion — leave that change untouched. Use explicit `git add` paths, never `-A`/`.`.
- Prefer AUTO-FIX for whitespace/format rules (`markdownlint-cli2 --fix` handles MD012,
  MD022, MD030, MD031, MD032, MD038, MD040, MD060). Do NOT hand-rewrite narrative content.
- For rules that fight a doc's legitimate format, relax the RULE in
  `.config/.markdownlint.yml` rather than mangling content:
  - `MD024` (duplicate headings) — JOURNAL.md is an append-only log with intentionally
    repeated headings; set `MD024: siblings_only: true`, and if that is insufficient,
    disable MD024 for `JOURNAL.md` via a per-file ignore.
  - `MD036` (emphasis-as-heading) — JOURNAL.md uses bold lead-ins intentionally; disable
    `MD036`.
  - `MD041` (first-line h1) and `MD025` (single h1) — GitHub issue/PR templates legitimately
    lack/repeat an h1; disable these for `.github/**` (markdownlint-cli2 supports a
    `.github` glob ignore, or disable the rules globally if simpler and harmless here).
- Ignore internal working docs so the committed spec/plan need not be lint-clean: add
  `docs/superpowers/` (and `.superpowers/`, already gitignored) to markdownlint's ignore
  set. Choose the mechanism markdownlint-cli2 supports with the current `--config
  .config/.markdownlint.yml` invocation (e.g. a `globs`/`ignores` key in the config, or a
  `.markdownlintignore`). Verify it actually takes effect.
- CHANGELOG.md is release-please-managed; a plain MD012 (multiple-blank-lines) auto-fix is
  fine, but do not restructure it.

- [ ] **Step 1: Fix taplo-lint (drop the broken catalog fetch)**

In `prek.toml`, the `taplo-lint` hook currently has
`args = ["--config", ".config/.taplo.toml", "--default-schema-catalogs"]`. Remove the
`"--default-schema-catalogs"` entry so it reads
`args = ["--config", ".config/.taplo.toml"]` (matches `poe style`'s taplo invocation, which
already passes). Verify:

```bash
uv run prek run taplo-lint --all-files
```

Expected: Passed.

- [ ] **Step 2: Stop ruff from formatting Markdown (fixes `poe style`)**

`ruff 0.16.0` formats Python code blocks embedded in `*.md` when run as `ruff format .`,
which fails on `JOURNAL.md`. Exclude Markdown from ruff in `pyproject.toml` `[tool.ruff]`:

```toml
[tool.ruff]
line-length = 100
target-version = "py314"
extend-exclude = ["*.md"]
```

Verify:

```bash
uv run ruff format --check .
```

Expected: exit 0 ("N files already formatted"), with no `.md` file listed.

- [ ] **Step 3: Auto-fix markdownlint, then relax rules for narrative/template docs**

Run the auto-fixer, then inspect what remains:

```bash
uv run markdownlint-cli2 --fix --config .config/.markdownlint.yml "**/*.md"
uv run prek run markdownlint-cli2 --all-files
```

For every residual violation, apply the policy above (relax the rule in
`.config/.markdownlint.yml` for narrative/template cases; minimal content fix only for
user-facing docs where a rule is legitimate). Re-run `uv run prek run markdownlint-cli2
--all-files` until it reports Passed.

- [ ] **Step 4: Add markdownlint ignore for internal docs, then stage & commit docs**

Configure markdownlint to ignore `docs/superpowers/` (per policy), then:

```bash
git add prek.toml pyproject.toml .config/.markdownlint.yml \
        README.md AGENTS.md CHANGELOG.md JOURNAL.md .github \
        docs/superpowers
git status   # confirm GEMINI.md deletion is NOT staged; no stray files staged
```

Do NOT `git add -A`. Confirm the staged set is only intended files (the ones you changed
plus `docs/superpowers/**`), and that `GEMINI.md` remains unstaged-deleted.

- [ ] **Step 5: Full green verification**

```bash
uv run prek run --all-files --show-diff-on-failure
uv run poe style
```

Expected: prek reports every hook Passed; `poe style` exits 0.

- [ ] **Step 6: Commit**

```bash
git commit -m "chore: satisfy markdownlint/taplo across docs and adopt project spec+plan

Clear pre-existing lint debt the new prek-based CI will enforce: drop taplo's broken
schema-catalog fetch, stop ruff formatting Markdown, auto-fix/relax markdownlint for
narrative and GitHub-template docs, and commit the design spec and implementation plan."
```

---

## Task 5: CI restructure (prek job, SHA pins, coverage/Codecov)

**Files:**

- Rewrite: `.github/workflows/ci.yml`
- Modify: `.github/workflows/check-pr-title.yml` (SHA-pin actions)
- Create: `.github/codecov.yml`

**Interfaces:**

- Consumes: Task 1 (dynamic version — CI must not assume a static literal), Task 2
  (pinned deps used by `uv sync --frozen`), and Task 4 (the prek suite is now green, so the
  new `hooks` job can pass).
- Produces: none.

- [ ] **Step 1: Add Codecov config**

Create `.github/codecov.yml`:

```yaml
---
coverage:
  status:
    project:
      default:
        target: auto
        threshold: 1%
    patch:
      default:
        target: auto
        threshold: 1%
comment:
  layout: "reach, diff, flags, files"
  behavior: default
  require_changes: false
flag_management:
  default_rules:
    carryforward: true
```

- [ ] **Step 2: Rewrite `ci.yml` — hooks + test + typecheck**

Replace `.github/workflows/ci.yml` with:

```yaml
---
name: CI
on:
  workflow_dispatch:
  push:
    branches: [main]
  pull_request:
    branches: [main]
permissions:
  contents: read
jobs:
  hooks:
    name: Run prek hooks
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9  # v9.0.0
        with:
          enable-cache: true
          cache-dependency-glob: |
            pyproject.toml
            uv.lock
      - name: Set up Python
        run: uv python install 3.14
      - run: uv run --locked prek run --all-files --show-diff-on-failure
  test:
    name: Test (Python ${{ matrix.python-version }} on ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.14"]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9  # v9.0.0
        with:
          enable-cache: true
          cache-dependency-glob: |
            pyproject.toml
            uv.lock
      - name: Set up Python
        run: uv python install ${{ matrix.python-version }}
      - name: Configure git identity (required by tests that init repos)
        run: |
          git config --global user.email "ci@example.com"
          git config --global user.name "CI"
      - name: Install dependencies
        run: uv sync --all-extras --frozen
      - name: Run tests
        run: uv run --locked pytest -v --cov-report=xml
      - name: Upload coverage to Codecov
        if: matrix.os == 'ubuntu-latest'
        uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f  # v7.0.0
        with:
          files: ./coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}
  typecheck:
    name: Type check (${{ matrix.tool }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        tool: [mypy, pyright, ty, pyrefly, pylint, vulture, slotscheck]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9  # v9.0.0
        with:
          enable-cache: true
          cache-dependency-glob: |
            pyproject.toml
            uv.lock
      - name: Set up Python
        run: uv python install 3.14
      - name: Install dependencies
        run: uv sync --all-extras --frozen
      - name: Run ${{ matrix.tool }}
        run: |
          case "${{ matrix.tool }}" in
            mypy)       uv run --locked mypy ;;
            pyright)    uv run --locked pyright ;;
            ty)         uv run --locked ty check ;;
            pyrefly)    uv run --locked pyrefly check ;;
            pylint)     uv run --locked pylint src ;;
            vulture)    uv run --locked vulture ;;
            slotscheck) uv run --locked slotscheck -m olink ;;
          esac
```

(The old standalone `lint` job is gone — `hooks` covers ruff/typos/taplo/validate-pyproject
- more via `prek.toml`.)

- [ ] **Step 3: SHA-pin the PR-title workflow**

In `.github/workflows/check-pr-title.yml` replace the three `uses:` lines:

- `amannn/action-semantic-pull-request@v6` →
  `amannn/action-semantic-pull-request@48f256284bd46cdaab1048c3721360e808335d50  # v6.1.1`
- both `marocchino/sticky-pull-request-comment@v3.0.5` →
  `marocchino/sticky-pull-request-comment@5770ad5eb8f42dd2c4f34da00c94c5381e49af88  # v3.0.5`

- [ ] **Step 4: Verify workflow validity**

Run:

```bash
uv run prek run --all-files --show-diff-on-failure   # check-yaml validates the workflows
# Optional stronger check if available:
command -v actionlint >/dev/null && actionlint .github/workflows/*.yml || echo "actionlint not installed; skipped"
grep -rn "@v[0-9]" .github/workflows/*.yml && echo "UNPINNED TAG REMAINS (check)" || echo "all actions SHA-pinned"
```

Expected: prek passes; no `@vN` floating tags remain in the workflow files (every `uses:`
is a SHA + comment).

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/check-pr-title.yml .github/codecov.yml
git commit -m "ci: consolidate lint into a prek job, SHA-pin actions, add Codecov

Restructure CI into hooks/test/typecheck, run installs with --frozen and tools with
--locked, emit coverage.xml and upload from ubuntu, and pin every action to a commit SHA."
```

---

## Task 6: Final full verification

**Files:** none (verification only).

- [ ] **Step 1: Clean-environment sanity pass**

Run:

```bash
uv sync --all-extras
uv run poe style
uv run poe typecheck
uv run poe test
uv run prek run --all-files --show-diff-on-failure
uv build --no-sources --quiet && ls dist/
grep -rn "x-release-please-version" . --exclude-dir=.git --exclude-dir=docs || echo "marker gone (good)"
```

Expected: all green (`poe style` and `prek` both exit 0 after Task 4); `dist/` contains a
wheel + sdist whose version is the tag-derived value (or `0.0.0` fallback on a tagless
checkout); the `x-release-please-version` marker is absent from source/config (it may still
appear in `docs/` prose describing the migration — that is expected).

- [ ] **Step 2: Confirm the tree state**

Run:

```bash
git status --porcelain
```

Expected: the ONLY entry is `D GEMINI.md` (intentionally left deleted-and-unstaged per the
user decision; `.superpowers/` is gitignored). Everything else from Tasks 1–5 is committed.
If any other change remains uncommitted, it belongs to one of the earlier task commits —
resolve it before finishing.

---

## Self-Review notes

- **Spec coverage:** §1 → Task 1; §2.1/2.3/§3.3/§3.4 → Task 2; §2.2 (.gitattributes) +
  §3.5 (.vscode) → Task 3; pre-existing lint-debt cleanup + docs commit (added mid-run) →
  Task 4; §2.4 (codecov) + §3.1 (SHA pins) + §3.2 (--frozen/--locked) + §4 (CI restructure)
  → Task 5; §whole-change verification → Task 6. All spec sections map to a task.
- **Task-runner constraint:** poe retained; no tox anywhere. ✓
- **prek.toml:** not downgraded; only a possible `check-json` exclude added (Task 3 Step 4)
  if `launch.json` comments trip the builtin. ✓
- **Type/name consistency:** the only produced symbol is `olink.__version__` (Task 1),
  consumed by the existing `olink/cli/app.py` import — unchanged and consistent. ✓
