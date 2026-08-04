# olink

[![CI](https://github.com/hasansezertasan/olink/actions/workflows/ci.yml/badge.svg)](https://github.com/hasansezertasan/olink/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/hasansezertasan/olink)](https://codecov.io/gh/hasansezertasan/olink)
[![Documentation Status](https://img.shields.io/github/deployments/hasansezertasan/olink/github-pages?label=docs)](https://hasansezertasan.github.io/olink)
[![PyPI - Version](https://img.shields.io/pypi/v/olink.svg)](https://pypi.org/project/olink)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/olink.svg)](https://pypi.org/project/olink)
[![License - MIT](https://img.shields.io/github/license/hasansezertasan/olink.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/hasansezertasan/olink?style=social)](https://github.com/hasansezertasan/olink/stargazers)
[![Latest Commit](https://img.shields.io/github/last-commit/hasansezertasan/olink)](https://github.com/hasansezertasan/olink)

[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://www.mypy-lang.org/)
[![linting - Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/hasansezertasan/olink/badge)](https://scorecard.dev/viewer/?uri=github.com/hasansezertasan/olink)
[![GitHub Tag](https://img.shields.io/github/tag/hasansezertasan/olink?include_prereleases=&sort=semver&color=black)](https://github.com/hasansezertasan/olink/releases/)

[![Downloads](https://pepy.tech/badge/olink)](https://pepy.tech/project/olink)
[![Downloads/Month](https://pepy.tech/badge/olink/month)](https://pepy.tech/project/olink)
[![Downloads/Week](https://pepy.tech/badge/olink/week)](https://pepy.tech/project/olink)

> A CLI tool that opens external URLs related to your project.

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Available Targets](#available-targets)
- [Examples](#examples)
- [Interactive TUI](#interactive-tui)
- [Limitations](#limitations)
- [Requirements](#requirements)
- [Motivation](#motivation)
- [Features](#features)
- [Support](#support-heart)
- [Analysis](#analysis)
- [Contributing](#contributing-heart)
- [Development](#development-toolbox)
- [Releasing](#releasing)
- [Author](#author-person_with_crown)
- [Credits](#credits)
- [License](#license-scroll)
- [Changelog](#changelog-memo)

## Installation

```bash
uv tool install olink            # CLI only
uv tool install 'olink[tui]'     # Include the interactive TUI
```

Or with `pipx`:

```bash
pipx install olink
pipx install 'olink[tui]'
```

## Usage

```bash
olink <target>              # Open a target URL
olink -n <target>           # Dry-run: print URL without opening
olink -d /path <target>     # Use a different project directory
olink --list                # List targets available for current project
olink --list-all            # List all targets
olink --version             # Show olink version
```

## Available Targets

### Git Targets

Automatically detects GitHub, GitLab, Bitbucket, Gitea, and Forgejo (incl. Codeberg) from your remote URL. Self-hosted instances are detected by hostname keyword matching.

| Target        | Description                          |
| ------------- | ------------------------------------ |
| `origin`      | Open the remote origin URL           |
| `upstream`    | Open the upstream remote URL         |
| `issues`      | Open the issues page                 |
| `pulls`       | Open pull/merge requests page        |
| `actions`     | Open CI/CD page (Actions, Pipelines) |
| `wiki`        | Open the wiki page                   |
| `releases`    | Open the releases page               |
| `branches`    | Open the branches page               |
| `commits`     | Open the commit history              |
| `security`    | Open the security page               |
| `discussions` | Open the discussions page            |

#### Supported Platforms

| Platform  | Issues      | PRs/MRs             | CI/CD          | Wiki       | Releases      |
| --------- | ----------- | ------------------- | -------------- | ---------- | ------------- |
| GitHub    | `/issues`   | `/pulls`            | `/actions`     | `/wiki`    | `/releases`   |
| GitLab    | `/-/issues` | `/-/merge_requests` | `/-/pipelines` | `/-/wikis` | `/-/releases` |
| Bitbucket | `/issues`   | `/pull-requests`    | `/pipelines`   | `/wiki`    | `/downloads`  |

**Note:** Some features are platform-specific:

- `discussions` is GitHub-only
- `security` is not available on Bitbucket, Gitea, or Forgejo
- Gitea/Forgejo paths mirror GitHub (`/issues`, `/pulls`, `/releases`, etc.)

**SSH aliases (`insteadOf`):** olink honors `[url "<rewritten>"].insteadOf = <prefix>` rules
in `.git/config`. Longest-prefix match wins, matching git's own behavior. This means
shorthand remotes like `github:owner/repo` resolve correctly when you have:

```ini
[url "git@github.com:"]
    insteadOf = github:
```

### Python / PyPI Targets

| Target      | Description                     | Config File      |
| ----------- | ------------------------------- | ---------------- |
| `pypi`      | Open PyPI page                  | `pyproject.toml` |
| `inspector` | Open PyPI Inspector             | `pyproject.toml` |
| `pypi-json` | Open PyPI JSON API              | `pyproject.toml` |
| `pepy`      | Open PePy download stats        | `pyproject.toml` |
| `piwheels`  | Open piwheels project page      | `pyproject.toml` |
| `pypistats` | Open PyPI Stats                 | `pyproject.toml` |
| `piptrends` | Open Pip Trends                 | `pyproject.toml` |
| `clickpy`   | Open ClickPy stats (ClickHouse) | `pyproject.toml` |
| `safety-db` | Open Safety DB vulnerabilities  | `pyproject.toml` |

### Multi-Ecosystem Targets

These services support multiple ecosystems (Python, npm, Rust, Go).

| Target         | Description                        | Ecosystems           |
| -------------- | ---------------------------------- | -------------------- |
| `snyk`         | Open Snyk security advisor         | pypi, npm, cargo, go |
| `libraries-io` | Open Libraries.io                  | pypi, npm, cargo, go |
| `deps`         | Open deps.dev (Google Open Source) | pypi, npm, cargo, go |
| `ecosystems`   | Open ecosyste.ms                   | pypi, npm, cargo, go |
| `socket`       | Open Socket.dev package health     | pypi, npm, cargo, go |

**Suffix Notation:** For projects with multiple ecosystems, use `target:ecosystem`:

```bash
olink snyk:pypi     # Explicit Python
olink snyk:npm      # Explicit npm
olink deps:cargo    # Explicit Rust
```

If only one ecosystem is detected, the suffix is optional and auto-detection is used.

### npm Targets

| Target          | Description                     | Config File    |
| --------------- | ------------------------------- | -------------- |
| `npm`           | Open npm page                   | `package.json` |
| `bundlephobia`  | Open Bundlephobia (bundle size) | `package.json` |
| `packagephobia` | Open Packagephobia (install)    | `package.json` |
| `npm-stat`      | Open npm-stat download charts   | `package.json` |
| `jsdelivr`      | Open jsDelivr package page      | `package.json` |
| `unpkg`         | Open UNPKG package page         | `package.json` |
| `skypack`       | Open Skypack package page       | `package.json` |

### Rust Targets

| Target   | Description                       | Config File  |
| -------- | --------------------------------- | ------------ |
| `crates` | Open crates.io page               | `Cargo.toml` |
| `librs`  | Open lib.rs (alternative browser) | `Cargo.toml` |
| `docsrs` | Open docs.rs API docs             | `Cargo.toml` |

### Go Targets

| Target    | Description                   | Config File |
| --------- | ----------------------------- | ----------- |
| `pkg-go`  | Open pkg.go.dev module page   | `go.mod`    |
| `go-docs` | Open pkg.go.dev documentation | `go.mod`    |

### Other Ecosystem Targets

| Target           | Description                      | Config File                              |
| ---------------- | -------------------------------- | ---------------------------------------- |
| `packagist`      | Open Packagist (PHP)             | `composer.json`                          |
| `pub`            | Open pub.dev (Dart)              | `pubspec.yaml`                           |
| `gems`           | Open RubyGems                    | `*.gemspec`                              |
| `rubygems-stats` | Open RubyGems download stats     | `*.gemspec`                              |
| `open-vsx`       | Open the Open VSX extension page | `package.json`                           |
| `maven`          | Open Maven Central artifact page | `pom.xml`                                |
| `hackage`        | Open Hackage package page        | `*.cabal`                                |
| `cpan`           | Open MetaCPAN module page        | `Makefile.PL`, `dist.ini`, or `lib/*.pm` |
| `hex`            | Open hex.pm (Elixir)             | `mix.exs`                                |
| `nuget`          | Open NuGet (.NET)                | `*.csproj`                               |

### Service Targets

| Target      | Description         |
| ----------- | ------------------- |
| `codecov`   | Open Codecov page   |
| `coveralls` | Open Coveralls page |

## Examples

```bash
# Open the GitHub repo for your project
olink origin

# Open issues page
olink issues

# Check the PyPI page for your package
olink pypi

# View download stats on PePy
olink pepy

# Check security vulnerabilities on Snyk
olink snyk

# In a monorepo with Python + npm, use explicit ecosystem
olink snyk:pypi      # Check Python package on Snyk
olink deps:npm       # View npm deps on deps.dev
olink socket:npm     # Check npm package health on Socket.dev

# View dependency graph on deps.dev
olink deps

# Check npm bundle size
olink bundlephobia

# Open releases page
olink releases

# Open code coverage
olink codecov

# Preview URL without opening browser
olink -n pulls

# Open origin for a different project
olink -d ~/projects/other-project origin

# See which targets work for your project
olink --list
```

## Interactive TUI

Launch the interactive target browser with:

```bash
olink                # Open TUI (requires [tui] extra)
```

The TUI lets you browse, search, open, and pin targets interactively. Keybindings:

- `Tab` — toggle view (available/all)
- `j`/`k` — navigate up/down
- `/` — search targets
- `o` — open the highlighted target
- `c` — copy target URL
- `p` — pin/unpin the highlighted target. Pinned targets are marked with `★`
  and float to the top of the list in every project. Pins are stored in
  `$XDG_CONFIG_HOME/olink/pins.json` (default `~/.config/olink/pins.json`).
- `q` — quit

## Limitations

- olink must be run from the project root directory. Running from a subdirectory (e.g. `src/`) is not supported.

## Requirements

- Python 3.14+

## Motivation

The metadata for any project already lives in files you keep in the repo — the git
remote in `.git/config`, the package name in `pyproject.toml`, `package.json`,
`Cargo.toml`, and friends. Yet the pages you actually want to visit (the PyPI page,
the issue tracker, download stats, a security advisor) are scattered across dozens
of hosts, each with its own URL shape. olink reads those files directly and opens
the right page for you — no bookmarks to maintain, no URLs to memorize, and it works
the same way in every project you `cd` into.

## Features

- **Zero configuration**: Detects your platform and package name from files already
  in the repo (`.git/config`, `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, …).
- **Wide platform coverage**: GitHub, GitLab, Bitbucket, Gitea, and Forgejo (incl.
  Codeberg), with self-hosted instances detected by hostname.
- **Many ecosystems**: Python, npm, Rust, Go, PHP, Dart, Ruby, Java/Maven, Haskell,
  Perl, Elixir, and .NET package registries and stats services.
- **Interactive TUI**: Browse, search, open, copy, and pin targets from a Textual
  terminal interface (via the `[tui]` extra).
- **File I/O over subprocess**: Reads config files directly instead of shelling out
  to `git`/`npm`, so it is fast and dependency-light.
- **Type Safety**: Full type hints checked by mypy and basedpyright.
- **Modern Python**: uv for dependency management, hatch for building.

## Support :heart:

If you have any questions or need help, feel free to open an issue on the [GitHub repository][olink].

## Analysis

- [Snyk Python Package Health Analysis](https://snyk.io/advisor/python/olink)
- [Libraries.io - PyPI](https://libraries.io/pypi/olink)
- [Safety DB](https://data.safetycli.com/packages/pypi/olink)
- [PePy Download Stats](https://www.pepy.tech/projects/olink)
- [PyPI Download Stats](https://pypistats.org/packages/olink)
- [Pip Trends Download Stats](https://piptrends.com/package/olink)
- [PyPI Map Dependency Graph](https://pypimap.com/package/olink)

## Contributing :heart:

Any contributions are welcome! Please follow the [Contributing Guidelines](./.github/CONTRIBUTING.md) to contribute to this project.

## Development :toolbox:

Clone the repository and cd into the project directory:

```sh
git clone https://github.com/hasansezertasan/olink
cd olink
```

### Install

Install the dependencies:

```sh
uv sync
```

### Style

Run the style checks:

```sh
uv run --locked tox run -e style
```

### Hooks

Run the prek hooks (a separate CI job, not part of `tox run`):

```sh
uv run --locked tox run -e prek
```

### CI

Run the test pipeline (the `style`, `cli`, and `3.14` tox environments):

```sh
uv run --locked tox run
```

To reproduce the full CI locally, run the hooks command above as well — CI runs
prek hooks in a separate job.

### Docs

Build the documentation site:

```sh
uv run --locked tox run -e docs-build
```

Start the live-reloading docs server:

```sh
uv run --locked tox run -e docs-server
```

## Releasing

Versioning and releases are automated with [release-please](https://github.com/googleapis/release-please), driven by [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/) PR titles squash-merged into `main`. release-please maintains a release PR that bumps the version and `CHANGELOG.md`; merging it tags the release and publishes to PyPI. See the [Contributing Guidelines](./.github/CONTRIBUTING.md#releasing) for the commit conventions and the one-time [Repository setup](./.github/CONTRIBUTING.md#repository-setup-one-time) (squash-merge settings, Actions permissions, release immutability, and PyPI trusted publishing).

## Author :person_with_crown:

This project is maintained by [Hasan Sezer Taşan][author]. It's me :wave:

## Credits

This package was created with [Copier](https://github.com/copier-org/copier) and the [hasansezertasan/copier-pyproject](https://github.com/hasansezertasan/copier-pyproject) project template.

## License :scroll:

This project is licensed under the [MIT License](https://spdx.org/licenses/MIT.html).

## Changelog :memo:

For a detailed list of changes, please refer to the [CHANGELOG](./CHANGELOG.md).

<!-- Refs -->
[author]: https://github.com/hasansezertasan
[olink]: https://github.com/hasansezertasan/olink
