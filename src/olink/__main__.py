"""Module entrypoint for the project.

This is the single runnable entrypoint used by ``python -m olink``
and by every standalone-executable build (PyCrucible launcher, PyInstaller
freezer, Nuitka compiler — see ADR-007). The build tools all target this file,
so the component-selection logic lives here and nowhere else.

The enabled component with the highest precedence — CLI > GUI > TUI > web > MCP >
worker — is wired to ``main()`` at template-generation time (via the Jinja
conditionals below), so this file contains exactly one component's launch code,
not a runtime dispatch. To change the default entrypoint, re-render with a
different component enabled or edit the import/``main`` binding here directly.
With no runnable component enabled, ``main()`` exits non-zero with an
explanatory message.
"""

from olink.cli import app


# The dispatchers below carry `# pragma: no cover`: invoking them launches the
# blocking component (CLI loop, GUI mainloop, server, ...), which cannot run
# under headless CI. tests/test_main.py pins the import wiring and callability.
def main() -> None:  # pragma: no cover
    """Run the CLI application."""
    app()


__all__ = ["main"]


if __name__ == "__main__":
    main()
