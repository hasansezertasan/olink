<<<<<<< before updating
"""CLI interface for olink.

Every action is a subcommand of the single ``olink`` Typer root, so each carries
its own ``--help`` and ``--json`` contract. Under ``--json`` stdout holds exactly
one JSON document (errors included), so agents can parse it without scraping
prose. Secondary components (``olink interactive`` for the TUI) are
lazily-imported subcommands rather than separate ``olink-<name>`` console scripts
(see https://hasansezertasan.github.io/copier-pyproject/context/components/#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts).
=======
"""CLI application for the project.

The ``olink`` command is the single Typer root. Every enabled
component other than the primary (CLI > GUI > TUI > web > MCP > worker) is hung
off it as a lazily-imported subcommand — ``olink interactive``
(TUI), ``olink web``, ``olink mcp``, ... — rather
than a separate ``olink-<name>`` console script.
>>>>>>> after updating
"""

import contextlib
import json
import logging
import platform
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer
from typer._click.exceptions import UsageError  # noqa: PLC2701 - Typer uses its bundled Click
from typer.core import TyperGroup

from olink import __version__
from olink.core.catalog import get_target, list_available_targets, list_targets
from olink.core.exceptions import (
    InvalidDirectoryError,
    NoRemoteError,
    NotGitRepoError,
    OlinkError,
    ProjectMetadataError,
    UnknownPlatformError,
    UnknownTargetError,
    UnsupportedFeatureError,
)

if TYPE_CHECKING:
<<<<<<< before updating
    from collections.abc import Generator, Mapping

    from typer._click.core import Context

__all__ = ["main"]


logger = logging.getLogger(__name__)

_TUI_OPTIONAL_DEPS = frozenset({"olink.tui", "textual", "pyperclip"})

# Distinct exit codes let a caller branch on the failure without parsing text.
# 1 is the generic OlinkError and 2 is Typer's own usage error, so start at 3.
EXIT_CODES: dict[type[OlinkError], int] = {
    UnknownTargetError: 3,
    InvalidDirectoryError: 4,
    NotGitRepoError: 5,
    NoRemoteError: 6,
    ProjectMetadataError: 7,
    UnsupportedFeatureError: 8,
    UnknownPlatformError: 9,
}


class _JsonGroup(TyperGroup):
    """Preserve machine-readable errors before command callbacks are entered."""

    def invoke(self, ctx: Context) -> object:
        arguments = ctx.args
        if "--" in arguments:
            arguments = arguments[: arguments.index("--")]
        as_json = "--json" in arguments
        try:
            return super().invoke(ctx)
        except UsageError as error:
            if not as_json:
                raise
            _emit({"error": {"type": type(error).__name__, "message": error.format_message()}})
            raise typer.Exit(error.exit_code) from error


app = typer.Typer(
    name="olink",
    help="Open external URLs related to your project.",
    no_args_is_help=True,
    cls=_JsonGroup,
)

_Directory = Annotated[
    (
        str | None,
        typer.Option(
            "--directory", "-d", help="Project directory (defaults to current directory)."
        ),
    )
]
_Json = Annotated[
    (bool, typer.Option("--json", help="Print a single JSON document on stdout instead of text."))
]
_Target = Annotated[
    (
        str,
        typer.Argument(help="Target name (e.g. origin, issues, pypi, snyk:npm). See `olink list`."),
    )
]


def _emit(payload: Mapping[str, object]) -> None:
    typer.echo(json.dumps(payload, indent=2))
=======
    from collections.abc import Generator

__all__ = ["app", "info", "interactive", "show_version"]

logger = get_logger()

# Every component's runtime dependency is a core ``dependency`` of this package
# (there are no per-component extras), so a missing one never means "install the
# extra" -- it means this environment is out of sync with the installed metadata.
# That happens after a component is enabled without a re-sync, or in a stale venv.
_MISSING_DEPENDENCY = "Error: The {component} component requires '{missing}', which is not available in this environment. {hint}"  # noqa: E501
_SYNC_HINT = f"Component dependencies ship with '{PROJECT_NAME}', so this usually means your environment is out of sync -- run `uv sync` (or reinstall the package) and try again."  # noqa: E501
_TUI_DEPENDENCIES = ("textual", "typing_extensions")


def _preflight(module: str) -> None:
    """Import a component dependency eagerly, so the guard below can classify it.

    Two kinds of dependency never reach the guard in a usable form. ``uvicorn``
    and Tkinter are imported at *call* time -- after the guarded block has closed
    -- and ``faststream.<broker>`` is a guarded re-export that raises a plain,
    *nameless* ``ImportError`` when the broker extra is absent, which exact-name
    matching cannot classify. Importing here, and supplying the module name when
    the interpreter does not, puts both back in reach of the guard.

    Args:
        module: Import module name to import eagerly.

    Raises:
        ModuleNotFoundError: Naming ``module`` when it cannot be imported.
    """
    try:
        _ = importlib.import_module(module)
    except ModuleNotFoundError as exc:
        # A nested failure belongs to the dependency being preflighted: a
        # partially installed uvicorn or web framework may name a sub-dependency
        # like ``click`` or ``starlette``, but the launcher's allowlist
        # intentionally knows only its direct dependencies.
        raise ModuleNotFoundError(str(exc), name=module) from None
    except ImportError as exc:
        # Not just "missing": a module whose own import raises is unusable here
        # too, and ``uv sync`` is the same repair. This is also the only shape
        # faststream's nameless broker-extra ``ImportError`` arrives in.
        raise ModuleNotFoundError(str(exc), name=module) from None
>>>>>>> after updating


@contextlib.contextmanager
def _reporting(*, as_json: bool) -> Generator[None]:
    """Turn an OlinkError into a typed exit code, as JSON or text."""
    try:
        yield
    except OlinkError as e:
        if as_json:
            _emit({"error": {"type": type(e).__name__, "message": str(e)}})
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(EXIT_CODES.get(type(e), 1)) from e


def _resolve_directory(directory: str | None) -> str:
    cwd = directory or str(Path.cwd())
    path = Path(cwd)
    if not path.exists():
        msg = f"Directory does not exist: {cwd}"
        raise InvalidDirectoryError(msg)
    if not path.is_dir():
        msg = f"Not a directory: {cwd}"
        raise InvalidDirectoryError(msg)
    return cwd


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"olink {__version__}")
        raise typer.Exit(0)


@app.callback()
def root(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Show olink version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Open external URLs related to your project."""


@app.command(name="open")
def open_target(target: _Target, directory: _Directory = None, as_json: _Json = False) -> None:
    """Open a target's URL in the browser."""
    with _reporting(as_json=as_json):
        resolved_url = get_target(target).get_url(_resolve_directory(directory))
    opened = typer.launch(resolved_url) == 0
    if as_json:
        _emit({"target": target, "url": resolved_url, "opened": opened})
    else:
        typer.echo(f"Opening: {resolved_url}")


@app.command()
def url(target: _Target, directory: _Directory = None, as_json: _Json = False) -> None:
    """Print a target's URL without opening it."""
    with _reporting(as_json=as_json):
        resolved = get_target(target).get_url(_resolve_directory(directory))
    if as_json:
        _emit({"target": target, "url": resolved})
    else:
        typer.echo(resolved)


@app.command(name="list")
def list_(
    all_targets: Annotated[
        bool,
        typer.Option("--all", "-a", help="List every target, not only those for this project."),
    ] = False,
    directory: _Directory = None,
    as_json: _Json = False,
) -> None:
    """List targets available for the current project."""
    rows: list[dict[str, str | None]]
    if all_targets:
        rows = [
            {"name": name, "description": description, "ecosystem": None}
            for name, description in list_targets()
        ]
    else:
        with _reporting(as_json=as_json):
            cwd = _resolve_directory(directory)
            rows = [
                {"name": name, "description": description, "ecosystem": ecosystem}
                for name, description, _, ecosystem in list_available_targets(cwd)
            ]

    if as_json:
        _emit({"scope": "all" if all_targets else "available", "count": len(rows), "targets": rows})
        return
    if not rows:
        typer.echo("No targets available for this project.")
        return
    typer.echo("All targets:\n" if all_targets else "Available targets for this project:\n")
    for row in rows:
        typer.echo(f"  {row['name']:16} - {row['description']}")
    if not all_targets:
        typer.echo(f"\n({len(rows)} targets available)")


@app.command()
def interactive(directory: _Directory = None) -> None:
    """Launch the interactive TUI (requires the tui extra)."""
    with _reporting(as_json=False):
        cwd = _resolve_directory(directory)
    try:
        from olink.tui import launch_tui  # pylint: disable=import-outside-toplevel
    except ImportError as e:
        if e.name not in _TUI_OPTIONAL_DEPS:
            raise
        typer.echo(
            "Error: TUI requires extra dependencies. Install with: "
            "pip install olink[tui]  (or: uv tool install 'olink[tui]')",
            err=True,
        )
        raise typer.Exit(1) from None

    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        launch_tui(cwd)


@app.command()
def version(_directory: _Directory = None, as_json: _Json = False) -> None:
    """Show the olink version."""
    if as_json:
        _emit({"version": __version__})
    else:
        typer.echo(f"olink {__version__}")


@app.command()
def info(_directory: _Directory = None, as_json: _Json = False) -> None:
    """Show version, Python and platform details (useful in bug reports)."""
    payload = {
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    if as_json:
        _emit(payload)
        return
    typer.echo(f"olink Version: {payload['version']}")
    typer.echo(f"Python Version: {payload['python']}")
    typer.echo(f"Platform: {payload['platform']}")


def main() -> None:
    """Entry point for the CLI."""
    app()
