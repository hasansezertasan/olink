"""CLI interface for olink."""

import logging
from pathlib import Path

import typer

from olink.core.catalog import get_target, list_available_targets, list_targets
from olink.core.exceptions import OlinkError

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="olink",
    help="Open external URLs related to your project.",
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    target: str | None = typer.Argument(
        None,
        help="Target to open (origin, upstream, issues, pulls, actions, pypi, npm, gems, crates)",
    ),
    directory: str | None = typer.Option(
        None,
        "--directory",
        "-d",
        help="Project directory (defaults to current directory)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Print URL without opening it",
    ),
    list_available_flag: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List targets available for current project",
    ),
    list_all_flag: bool = typer.Option(
        False,
        "--list-all",
        "-a",
        help="List all targets",
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

    # Handle --list flag (available targets for current project)
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

    # Handle --list-all flag
    if list_all_flag:
        typer.echo("All targets:\n")
        for name, description in list_targets():
            typer.echo(f"  {name:16} - {description}")
        raise typer.Exit(0)

    # If no target provided, launch TUI
    if target is None:
        from olink.tui import launch_tui

        try:
            launch_tui(cwd)
        except (KeyboardInterrupt, SystemExit):
            pass
        raise typer.Exit(0)

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
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app()
