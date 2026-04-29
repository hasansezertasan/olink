# Changelog

## 0.1.0 (TBD)

Initial PyPI release.

### 🚀 Features

- CLI for opening external URLs related to your project (PyPI, npm, GitHub, GitLab, Bitbucket, Gitea, Forgejo, …).
- Interactive TUI (optional via `pip install olink[tui]`).
- Multi-ecosystem targets with suffix notation (`snyk:pypi`, `deps:npm`, etc.).
- `--version` / `-V` CLI flag.
- Automated release flow: Release Please opens version-bump PRs from Conventional Commits; merging cuts the GitHub Release and tag, which fires PyPI publish via OIDC trusted publishing.

### 🛠 Build

- Hatchling build backend.
- `py.typed` marker (PEP 561).
- Strict mypy configuration.
- Ruff lint + format configuration.
- CI matrix (ubuntu, macos) on Python 3.14.
