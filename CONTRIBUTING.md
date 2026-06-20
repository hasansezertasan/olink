<!-- omit in toc -->

# Contributing to olink

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for the maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
>
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

<!-- omit in toc -->

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
  - [Commit Messages](#commit-messages)
  - [Branch Names](#branch-names)
  - [Pull Request Titles](#pull-request-titles)

## Code of Conduct

This project and everyone participating in it is governed by the
[olink Code of Conduct](https://github.com/hasansezertasan/olink/blob/main/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to <hasansezertasan@gmail.com>.

## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://github.com/hasansezertasan/olink#readme).

Before you ask a question, it is best to search for existing [Issues](https://github.com/hasansezertasan/olink/issues) and [Discussions](https://github.com/hasansezertasan/olink/discussions) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open a [Discussion](https://github.com/hasansezertasan/olink/discussions/categories/questions).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (Python, OS, shell), depending on what seems relevant.

## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
>
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project licence.

### Reporting Bugs

<!-- omit in toc -->

#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version (`uv tool upgrade olink` or `pipx upgrade olink`).
- Determine if your bug is really a bug and not an error on your side (e.g. wrong working directory, missing remote, malformed `pyproject.toml`).
- Search the [bug tracker](https://github.com/hasansezertasan/olink/issues?q=label%3Abug) to see if the issue has been reported already.
- Collect information about the bug:
  - The exact command you ran (e.g. `olink pypi`).
  - The full output / traceback.
  - Relevant snippets of the project file olink reads (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `.git/config`). Redact secrets.
  - OS, shell, Python version, olink version (`olink --version`).

<!-- omit in toc -->

#### How Do I Submit a Good Bug Report?

> Never report security related issues, vulnerabilities or bugs including sensitive information to the public issue tracker. Instead send them to <hasansezertasan@gmail.com>.

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/hasansezertasan/olink/issues/new/choose) using the **Bug report** template.
- Explain the behavior you would expect and the actual behavior.
- Provide the reproduction steps and information collected above.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for olink, **including completely new targets, new ecosystems, and minor improvements to existing functionality**.

<!-- omit in toc -->

#### Before Submitting an Enhancement

- Make sure you are running the latest version.
- Read the [README](https://github.com/hasansezertasan/olink#readme) carefully and check whether the functionality is already covered, possibly under a different target name.
- Search [existing issues](https://github.com/hasansezertasan/olink/issues) to see if the enhancement has already been suggested.
- Check the scope: olink aims to *open URLs related to your project*. Generic browser automation, scaffolding, or remote API calls are out of scope.

<!-- omit in toc -->

#### How Do I Submit a Good Enhancement Suggestion?

Open a [Feature request](https://github.com/hasansezertasan/olink/issues/new/choose) and:

- Use a **clear and descriptive title**.
- Provide a **step-by-step description** of the suggested enhancement.
- **Describe current behavior** and **explain the desired behavior**, with the exact command(s) and expected URL(s).
- **Explain why** this is useful to most olink users.

### Your First Code Contribution

1. Fork the repository.
1. Create a feature branch (see [Branch Names](#branch-names)).
1. Make your changes.
1. Add tests for new functionality.
1. Run the test suite and linters.
1. Submit a pull request (see [Pull Request Titles](#pull-request-titles)).

#### Dev Container (Recommended)

This repository includes a preconfigured dev container in `.devcontainer/`.

1. Install the VS Code **Dev Containers** extension.
1. Open the repository in VS Code.
1. Run **Dev Containers: Reopen in Container**.

The container installs Python 3.14, `uv`, and project dependencies automatically.

#### Development Commands

- `uv sync --all-extras` — install dependencies (incl. `tui` extra)
- `uv run olink <target>` — run the CLI
- `uv run pytest` — run all tests
- `uv run pytest -v` — verbose output
- `uv run pytest tests/cli/test_cli.py::TestCLIDryRun::test_dry_run_pypi` — single test
- `uv run pytest --cov=olink --cov-report=term-missing` — coverage report

If you have [poethepoet](https://poethepoet.natn.io/) installed (it is in the `tool` group):

- `uv run poe test` — run tests
- `uv run poe style` — run linters and formatters
- `uv run poe typecheck` — run all type checkers

#### Code Quality Commands

- `uv run ruff check .` — lint
- `uv run ruff format .` — format
- `uv run mypy` — primary type checker
- `uv run pyright` — secondary type checker
- `uv run ty check` — Astral's type checker
- `uv run pyrefly check` — Meta's type checker
- `uv run pylint src` — extra static analysis
- `uv run vulture` — dead code detection
- `uv run slotscheck -m olink` — `__slots__` correctness
- `uv run typos` — spell check
- `uv run validate-pyproject pyproject.toml` — manifest schema check
- `uv run taplo lint && uv run taplo format` — TOML lint/format

#### Build Commands

- `uv build` — build the package
- `uv publish` — publish to PyPI (release flow uses Trusted Publishing via CI)

### Improving The Documentation

Documentation lives in `README.md` and `JOURNAL.md`. PRs that clarify usage, fix typos, or add examples are very welcome.

## Styleguides

### Commit Messages

Follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/). Commit messages are the source of truth for releases: [release-please](https://github.com/googleapis/release-please) parses them on every push to `main` and maintains a "Release PR" with the computed version bump and changelog. Merging that PR cuts the git tag and a draft GitHub release, after which CI builds, publishes to PyPI via Trusted Publishing, and un-drafts the release. [hatch-vcs](https://github.com/ofek/hatch-vcs) reads the tag at build time to set the package version, so the version is never hand-edited.

Examples:

- `feat: add openapi target`
- `fix: handle gitea remotes correctly`
- `docs: clarify dry-run flag`
- `chore(deps): bump typer to 0.21.1`

### Branch Names

Follow [Conventional Branch](https://conventional-branch.github.io/). Examples: `feat/openapi-target`, `fix/gitea-remote`, `docs/clarify-dry-run`.

### Pull Request Titles

PR titles must follow Conventional Commits — they are linted by the `Lint PR` workflow.

<!-- omit in toc -->

## Attribution

This guide is based on the [contributing.md](https://contributing.md/generator) generator.
