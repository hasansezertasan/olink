"""Headless TUI information retrieval."""

from __future__ import annotations

from olink.tui.app import build_info_message


def tui_info() -> str:
    """Return the info message without starting the TUI.

    Returns:
        str: A multi-line project information summary.
    """
    return build_info_message()
