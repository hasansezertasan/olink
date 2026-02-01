"""Action handlers for the TUI."""

import webbrowser

import pyperclip


def open_in_browser(url: str) -> bool:
    """Open a URL in the default browser."""
    return webbrowser.open(url)


def copy_to_clipboard(url: str) -> bool:
    """Copy text to the system clipboard."""
    try:
        pyperclip.copy(url)
    except pyperclip.PyperclipException:
        return False
    return True
