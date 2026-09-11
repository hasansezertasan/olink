<<<<<<< before updating
"""CLI interface for olink."""
=======
"""CLI application for the project.

The ``olink`` command is the single Typer root. Every enabled
component other than the primary (CLI > GUI > TUI > web > MCP > worker) is hung
off it as a lazily-imported subcommand — ``olink interactive``
(TUI), ``olink web``, ``olink mcp``, ... — rather
than a separate ``olink-<name>`` console script (see ADR-019).
"""
# mypy: disable-error-code="misc"
>>>>>>> after updating

import contextlib
import logging
from pathlib import Path

import typer

from olink import __version__
from olink.core.catalog import get_target, list_available_targets, list_targets
from olink.core.exceptions import OlinkError

__all__ = ["main", "main_callback"]


logger = logging.getLogger(__name__)

_TUI_OPTIONAL_DEPS = frozenset({"olink.tui", "textual", "pyperclip"})

app = typer.Typer(
    name="olink", help="Open external URLs related to your project.", no_args_is_help=False
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"olink {__version__}")
        raise typer.Exit(0)


@app.callback(invoke_without_command=True)
def main_callback(
    target: str | None = typer.Argument(
        None,
        help="Target to open (e.g. origin, issues, pypi, npm, crates, and more — use --list-all to see all)",
    ),
    directory: str | None = typer.Option(
        None, "--directory", "-d", help="Project directory (defaults to current directory)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Print URL without opening it"),
    list_available_flag: bool = typer.Option(
        False, "--list", "-l", help="List targets available for current project"
    ),
    list_all_flag: bool = typer.Option(False, "--list-all", "-a", help="List all targets"),
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show olink version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Open external URLs related to your project."""
    cwd = directory or str(Path.cwd())

    cwd_path = Path(cwd)
    if not cwd_path.exists():
        typer.echo(f"Error: Directory does not exist: {cwd}", err=True)
        raise typer.Exit(1)
    if not cwd_path.is_dir():
        typer.echo(f"Error: Not a directory: {cwd}", err=True)
        raise typer.Exit(1)

    if list_available_flag:
        available = list_available_targets(cwd)

        if available:
            typer.echo("Available targets for this project:\n")
            for name, description, _, _ in available:
                typer.echo(f"  {name:16} - {description}")
            typer.echo(f"\n({len(available)} targets available)")
        else:
            typer.echo("No targets available for this project.")
        raise typer.Exit(0)

    if list_all_flag:
        typer.echo("All targets:\n")
        for name, description in list_targets():
            typer.echo(f"  {name:16} - {description}")
        raise typer.Exit(0)

    if target is None:
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
        raise typer.Exit(0)

<<<<<<< before updating
    try:
        target_instance = get_target(target)
        url = target_instance.get_url(cwd)

        if dry_run:
            typer.echo(url)
        else:
            typer.echo(f"Opening: {url}")
            typer.launch(url)
    except OlinkError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


def main() -> None:
    """Entry point for the CLI."""
    app()
=======
@app.command(name="version")
def show_version() -> None:
    """Show the current version number of olink.

    Show the version number:
        olink version

    Example output:
        0.1.0

    Raises:
        typer.Exit: If the package metadata cannot be found.
    """
    try:
        distribution = Distribution.from_name(PROJECT_NAME)
    except PackageNotFoundError:
        # An uninstalled or partial package is an expected, user-facing error, so
        # log without the traceback that logging.exception would add.
        logger.error("Package metadata not found for %s", PROJECT_NAME)  # noqa: TRY400
        typer.echo(
            f"Error: Package '{PROJECT_NAME}' metadata not found. Is the package installed correctly?",  # noqa: E501
            err=True,
        )
        raise typer.Exit(code=1) from None
    logger.info("Command `version` called.")
    typer.echo(distribution.version)
    logger.info("Version displayed successfully.")


@app.command()
def info() -> None:
    """Display information about the olink application.

    Show application information:
        olink info

    Example output:
        Application Version: 0.1.0
        Python Version: 3.12.0 (CPython)
        Platform: Darwin

    Raises:
        typer.Exit: If the package metadata cannot be found.
    """
    try:
        distribution = Distribution.from_name(PROJECT_NAME)
    except PackageNotFoundError:
        # An uninstalled or partial package is an expected, user-facing error, so
        # log without the traceback that logging.exception would add.
        logger.error("Package metadata not found for %s", PROJECT_NAME)  # noqa: TRY400
        typer.echo(
            f"Error: Package '{PROJECT_NAME}' metadata not found. Is the package installed correctly?",  # noqa: E501
            err=True,
        )
        raise typer.Exit(code=1) from None
    logger.info("Command `info` called.")
    python_version = platform.python_version()
    python_implementation = platform.python_implementation()
    typer.echo(f"Application Version: {distribution.version}")
    typer.echo(f"Python Version: {python_version} ({python_implementation})")
    typer.echo(f"Platform: {platform.system()}")
    logger.info("Application information displayed successfully.")


@app.command()
def interactive() -> None:  # pragma: no cover
    """Start interactive mode (TUI) for olink.

    Launch the terminal user interface:
        olink interactive

    Raises:
        typer.Exit: Propagating the TUI's exit code.
    """
    from olink.tui.app import main  # noqa: PLC0415

    raise typer.Exit(code=main())
>>>>>>> after updating
