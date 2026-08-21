"""Module entrypoint for the project.

This is the single runnable entrypoint used by ``python -m olink``
and by every standalone-executable build (PyCrucible launcher, PyInstaller
freezer, Nuitka compiler — see ADR-007). The build tools all target this file,
so the component-selection logic lives here and nowhere else.

When a ``olink`` console root exists (``include_console_root`` —
the CLI, or ≥2 components sharing a launcher; see ADR-019), ``main()`` runs it,
which dispatches to the primary component by default and to each secondary via a
subcommand. Otherwise the single enabled component with the highest precedence —
CLI > GUI > TUI > web > MCP > worker — is wired to ``main()`` directly at
template-generation time (via the Jinja conditionals below). To change the
default entrypoint, re-render with a different component enabled or edit the
import/``main`` binding here directly. With no runnable component enabled,
``main()`` exits non-zero with an explanatory message.
"""

from olink.cli import app


# The dispatchers below carry `# pragma: no cover`: invoking them launches the
# blocking component (CLI loop, GUI mainloop, server, ...), which cannot run
# under headless CI. tests/test_main.py pins the import wiring and callability.
def main() -> None:  # pragma: no cover
    """Run the olink console root (primary + component subcommands)."""
    app()


__all__ = ["main"]


if __name__ == "__main__":
    main()
