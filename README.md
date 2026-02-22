# olink

A CLI tool that opens external URLs related to your project.

## Installation

```bash
uv tool install olink
```

## Usage

```bash
olink <target>              # Open a target URL
olink -n <target>           # Dry-run: print URL without opening
olink -d /path <target>     # Use a different project directory
olink --list                # List all targets
olink --list-available      # List targets available for current project
```

## Available Targets

### Git Targets

Automatically detects GitHub, GitLab, and Bitbucket from your remote URL.

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
- `security` is not available on Bitbucket

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

### Rust Targets

| Target   | Description                       | Config File  |
| -------- | --------------------------------- | ------------ |
| `crates` | Open crates.io page               | `Cargo.toml` |
| `librs`  | Open lib.rs (alternative browser) | `Cargo.toml` |

### Other Ecosystem Targets

| Target      | Description          | Config File      |
| ----------- | -------------------- | ---------------- |
| `packagist` | Open Packagist (PHP) | `composer.json`  |
| `pub`       | Open pub.dev (Dart)  | `pubspec.yaml`   |
| `gems`      | Open RubyGems        | (directory name) |
| `hex`       | Open hex.pm (Elixir) | (directory name) |
| `nuget`     | Open NuGet (.NET)    | (directory name) |

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
olink --list-available
```

## Limitations

- olink must be run from the project root directory. Running from a subdirectory (e.g. `src/`) is not supported.

## Requirements

- Python 3.14+

## Development

See `JOURNAL.md` for a chronological record of decisions, attempts (including failures), and outcomes.

## License

MIT
