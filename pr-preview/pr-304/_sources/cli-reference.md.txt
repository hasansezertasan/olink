# CLI reference

The command-line interface below is generated on every docs build directly from
the live `olink.cli.app` Typer application (via `typer ... utils
docs`), so the documented commands, options, and defaults are always exactly what
the code exposes — they cannot drift from `--help`. The enabled component
subcommands (`web`/`gui`/`interactive`/`mcp`/`worker`) appear automatically, and only
when present.

```{include} _generated/cli.md
:heading-offset: 1
```
