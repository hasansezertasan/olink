"""CLI interface for olink.

Every action is a subcommand so each carries its own ``--help`` and ``--json``
contract. Under ``--json`` stdout holds exactly one JSON document (errors
included), so agents can parse it without scraping prose.
"""

import contextlib
import json
import logging
import platform
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import typer

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
    from collections.abc import Iterator

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

app = typer.Typer(
    name="olink", help="Open external URLs related to your project.", no_args_is_help=True
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


def _emit(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2))


@contextlib.contextmanager
def _reporting(*, as_json: bool) -> Iterator[None]:
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
        url = get_target(target).get_url(_resolve_directory(directory))
    opened = typer.launch(url) == 0
    if as_json:
        _emit({"target": target, "url": url, "opened": opened})
    else:
        typer.echo(f"Opening: {url}")


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
def version(as_json: _Json = False) -> None:
    """Show the olink version."""
    if as_json:
        _emit({"version": __version__})
    else:
        typer.echo(f"olink {__version__}")


@app.command()
def info(as_json: _Json = False) -> None:
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
