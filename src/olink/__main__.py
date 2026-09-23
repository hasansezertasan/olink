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

Either binding routes its import through a loader that turns a missing
dependency into one actionable line instead of a traceback (ADR-028). This is
the boundary that needs it most: a standalone executable's user has no console
root to fall back on and no obvious way to read a Python stack trace.
"""

import importlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# Each of these ships as a core dependency of this package, so a missing one
# never means "install an extra" -- it means this environment is out of sync with
# the installed metadata. A ``copier update`` that adds the shared launcher (or
# enables settings) adds both the code and its dependency at once, so an
# environment that has not been re-synced would otherwise fail here with a bare
# ``ModuleNotFoundError`` before any launcher code executes.
_ROOT_DEPENDENCIES = ("typer",)
_MISSING_ROOT_DEPENDENCY = "Error: The olink command requires the '{missing}' package, which is not installed. It ships with 'olink', so this usually means your environment is out of sync -- run `uv sync` (or reinstall the package) and try again."


def _preflight(module: str) -> None:
    """Import a dependency eagerly, attributing nested failures to it.

    Args:
        module: Import module name to verify eagerly.

    Raises:
        ModuleNotFoundError: Naming ``module`` when it cannot be imported.
    """
    try:
        _ = importlib.import_module(module)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(str(exc), name=module) from None
    except ImportError as exc:
        raise ModuleNotFoundError(str(exc), name=module) from None


def _load_console_root() -> Callable[[], None]:
    """Import the console root, reporting its own missing dependency actionably.

    Returns:
        Callable[[], None]: The console-root application. Both roots are
            zero-argument callables: the argparse ``app`` defaults its ``argv``,
            and ``typer.Typer.__call__`` takes ``*args``.

    Raises:
        ModuleNotFoundError: Propagating a missing module that is not exactly one
            of the root's own dependencies, so an unrelated import defect keeps
            its diagnostic context.
        SystemExit: With code 1 when one of them is missing from this environment.
    """
    try:
        for dependency in _ROOT_DEPENDENCIES:
            _preflight(dependency)
        from olink.cli import app
    except ModuleNotFoundError as exc:
        missing = exc.name
        if missing is None or missing not in _ROOT_DEPENDENCIES:
            raise
        _ = sys.stderr.write(_MISSING_ROOT_DEPENDENCY.format(missing=missing) + "\n")
        raise SystemExit(1) from None
    return app


# The dispatchers below carry `# pragma: no cover`: invoking them launches the
# blocking component (CLI loop, GUI mainloop, server, ...), which cannot run
# under headless CI. tests/test_main.py pins the import wiring and callability.
def main() -> None:  # pragma: no cover
    """Run the olink console root (primary + component subcommands)."""
    _load_console_root()()


__all__ = ["main"]


if __name__ == "__main__":
    main()
