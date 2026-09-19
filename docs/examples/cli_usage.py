"""CLI argument parsing."""

from __future__ import annotations

from olink.cli.app import app


def cli_app_name() -> str:
    """Return the registered CLI application name.

    Returns:
        str: The Typer application name.
    """
    return app.info.name or ""
