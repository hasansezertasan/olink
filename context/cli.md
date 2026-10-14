# CLI

## Subcommands with typed JSON errors

**Id:** b9d23728-2d7d-454c-9e0a-bdb234616f6d
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-10-08 (PR #281); `cli/app.py` (`EXIT_CODES`, `no_args_is_help`)

Every action is a subcommand (`open`, `url`, `list`, `interactive`,
`version`, `info`) rather than flags on one callback. Under `--json`,
stdout is exactly one JSON document — errors included — and each
`OlinkError` subclass maps to a distinct exit code (3–9), so scripts and
agents branch without scraping prose. `-d` lives on each command; `version`
and `info` accept and ignore it for uniform invocation. Bare `olink` prints
help; the TUI runs only via `olink interactive`.

**Reason:** flags could not give each action its own `--help`/`--json`
contract, and a positional target could not coexist with subcommand-aware
parsing. Machine-readable output plus typed codes is the agent contract.

**Rejected alternative:** keeping `--list`/`--list-all` flags with a
fallback that treats a bare positional as a target. Rejected because the
fallback needed custom Typer group metaprogramming (against the project's
simplicity rule) for a transitional convenience; the break was taken
cleanly as `feat!` instead.
