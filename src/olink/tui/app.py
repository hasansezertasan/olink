<<<<<<< before updating
"""Main TUI application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from olink.core.exceptions import OlinkError
from olink.core.pins import load_pins, save_pins
from olink.tui.actions import copy_to_clipboard, open_in_browser
from olink.tui.models import (
    FilterState,
    TargetItem,
    build_all_targets,
    build_available_targets,
    order_by_pins,
)
from olink.tui.widgets import SearchInput, StatusBar, TargetListWidget, TargetRow

__all__ = ["OlinkTUI", "launch_tui"]


HEADER_TEXT = (
    "olink — Interactive Target Browser\n"
    "Tab: toggle view  j/k: navigate  /: search  o: open  c: copy  p: pin  q: quit"
)


class OlinkTUI(App[None]):
    """Main TUI application managing state and widget composition."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "toggle_mode", "Toggle view", priority=True),
        Binding("o", "open_target", "Open"),
        Binding("c", "copy_target", "Copy"),
        Binding("p", "toggle_pin", "Pin"),
        Binding("slash", "start_search", "Search", show=False),
        Binding("escape", "cancel_search", "Cancel search", show=False),
    ]

    def __init__(self, cwd: str) -> None:
        super().__init__()
        self.cwd = cwd
        self.state = FilterState()
        self.all_targets = build_all_targets()
        self.available_targets = build_available_targets(cwd)
        self.searching = False
        self.pinned = load_pins()
        # Active search filter, kept after the search bar closes so a later
        # refresh (e.g. toggling a pin) does not silently drop the filter.
        self.active_query = ""

    def compose(self) -> ComposeResult:
        header = Static(HEADER_TEXT, id="header")
        header.styles.background = "darkblue"
        header.styles.color = "white"
        header.styles.text_style = "bold"
        header.styles.dock = "top"
        header.styles.height = 2
        yield header
        yield TargetListWidget()
        yield SearchInput()
        yield StatusBar()

    def on_mount(self) -> None:
        self._refresh_list()

    def _source(self) -> list[TargetItem]:
        base = self.available_targets if self.state.mode == "available" else self.all_targets
        return order_by_pins(base, self.pinned)

    def _refresh_list(self) -> None:
        items = self._filter_items(self.active_query)
        self.query_one(TargetListWidget).update_items(items)
        self._refresh_status(len(items))

    def _refresh_status(self, count: int | None = None) -> None:
        if count is None:
            count = len(self._filter_items(self.active_query))
        total = len(self.all_targets)
        self.query_one(StatusBar).status_update(self.state.mode, count, total)

    def action_toggle_mode(self) -> None:
        self.state.mode = "all" if self.state.mode == "available" else "available"
        self._end_search()
        self.active_query = ""
        self._refresh_list()

    def _filter_items(self, query: str) -> list[TargetItem]:
        """Filter current source items by substring match on name/description."""
        if not query:
            return self._source()
        q = query.lower()
        return [
            item
            for item in self._source()
            if q in item.name.lower() or q in item.description.lower()
        ]

    def _end_search(self) -> None:
        """Hide search input and reset search state."""
        search_input = self.query_one(SearchInput)
        search_input.value = ""
        search_input.display = False
        self.searching = False

    def action_start_search(self) -> None:
        """Show search input and focus it."""
        if self.searching:
            return
        self.searching = True
        search_input = self.query_one(SearchInput)
        search_input.display = True
        search_input.value = ""
        search_input.focus()

    def action_cancel_search(self) -> None:
        """Cancel search, restore full list, refocus target list."""
        if not self.searching:
            return
        self._end_search()
        self.active_query = ""
        self._refresh_list()
        self.query_one(TargetListWidget).focus()

    def on_input_changed(self, event: SearchInput.Changed) -> None:
        """Filter the target list as the user types in the search bar."""
        if not self.searching:
            return
        query = event.value
        self.active_query = query
        filtered = self._filter_items(query)
        self.query_one(TargetListWidget).update_items(filtered)
        status = self.query_one(StatusBar)
        if query:
            status.update(f" Search: '{query}' — {len(filtered)} matches")
            status.styles.color = "white"
        else:
            self._refresh_status()

    def on_input_submitted(self, _event: SearchInput.Submitted) -> None:
        """Confirm search: hide input, keep filtered list, refocus list."""
        if not self.searching:
            return
        # List is already filtered by on_input_changed; just close search UI
        self._end_search()
        target_list = self.query_one(TargetListWidget)
        count = len(target_list.children)
        self.query_one(StatusBar).status_update(self.state.mode, count, len(self.all_targets))
        target_list.focus()

    def _action_on_selected(self, action: str) -> None:
        item = self.query_one(TargetListWidget).get_selected_item()
        if item is None:
            return

        status = self.query_one(StatusBar)
        try:
            url = item.get_url(self.cwd)
        except OlinkError as e:
            status.set_error(str(e))
            return

        if action == "open":
            open_in_browser(url)
            status.set_success(f"Opened: {url}")
        elif action == "copy":
            if copy_to_clipboard(url):
                status.set_success(f"Copied: {url}")
            else:
                status.set_error("Clipboard not available")

    def action_open_target(self) -> None:
        self._action_on_selected("open")

    def action_copy_target(self) -> None:
        self._action_on_selected("copy")

    def action_toggle_pin(self) -> None:
        """Pin/unpin the highlighted target, persist, and keep it selected.

        The app's in-memory list is the session's source of truth: we toggle it
        first, then try to persist. If the write fails the change still stands
        (surfaced as an error), and a later successful toggle cannot silently
        drop it by reloading a stale file from disk.
        """
        target_list = self.query_one(TargetListWidget)
        item = target_list.get_selected_item()
        if item is None:
            return
        name = item.name
        if name in self.pinned:
            self.pinned = [existing for existing in self.pinned if existing != name]
        else:
            self.pinned = [*self.pinned, name]
        status = self.query_one(StatusBar)
        error: OSError | None = None
        try:
            save_pins(self.pinned)
        except OSError as exc:
            error = exc
        self._refresh_list()
        # Rows are re-mounted by update_items; wait for that to settle before
        # querying for the row to reselect.
        self.call_after_refresh(self._reselect, name)
        if error is not None:
            status.set_error(f"Could not save pins: {error}")
        else:
            verb = "Pinned" if name in self.pinned else "Unpinned"
            status.set_success(f"{verb} {name}")

    def _reselect(self, name: str) -> None:
        """Move the cursor back onto the row for `name` after a refresh."""
        target_list = self.query_one(TargetListWidget)
        for index, row in enumerate(target_list.query(TargetRow)):
            if row.item.name == name:
                target_list.index = index
                return


def launch_tui(cwd: str) -> None:
    """Entry point for the TUI."""
    OlinkTUI(cwd).run()
=======
"""TUI application for the project."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, ClassVar, final

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static
from typing_extensions import override

from olink.__metadata__ import PROJECT_NAME
from olink.core import app as service
from olink.core.logging_setup import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from textual.binding import BindingType

__all__ = ["InfoApp", "TuiDisplayError", "build_info_message", "main"]

logger = get_logger()


class TuiDisplayError(RuntimeError):
    """Raised when the TUI cannot be displayed."""


def build_info_message() -> str:
    """Return a short application information message for display.

    Returns:
        str: A multi-line summary of the project name, version, and platform.
    """
    payload = service.info_or_unknown()
    return (
        f"{PROJECT_NAME}\n\n"
        f"Version: {payload['application_version']}\n"
        f"Python: {payload['python_version']} ({payload['python_implementation']})\n"
        f"Platform: {payload['platform']}"
    )


@final
class InfoApp(App[None]):
    """Simple TUI application displaying project info."""

    CSS = """
    Screen {
        align: center middle;
        background: $surface;
    }

    #info-container {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $panel;
    }

    Static {
        width: 100%;
        height: auto;
        padding: 1;
    }

    #title {
        dock: top;
        height: 3;
        border-bottom: solid $primary;
        background: $boost;
        text-align: center;
        content-align: center middle;
    }

    #footer {
        dock: bottom;
        height: 1;
        border-top: solid $primary;
        text-align: center;
        background: $boost;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [("q", "quit", "Quit")]

    def __init__(self, message: str) -> None:
        """Initialize the application.

        Args:
            message: The formatted information message to display.
        """
        super().__init__()
        self.message = message

    @override
    def compose(self) -> ComposeResult:
        """Compose the TUI layout.

        Yields:
            Widget: The widgets that make up the screen layout.
        """
        yield Static(PROJECT_NAME, id="title")
        with ScrollableContainer(id="info-container"):
            yield Static(self.message, id="info-text")
        yield Static("Press 'q' to quit", id="footer")

    def on_mount(self) -> None:
        """Set focus and style on mount."""
        self.title = f"{PROJECT_NAME} Info"


def _run_app(app: InfoApp) -> None:  # pragma: no cover
    """Execute the Textual event loop.

    The irreducible blocking call separated from UI setup and error handling.
    """
    app.run()


def _display_tui(message: str, *, driver: Callable[[InfoApp], None] = _run_app) -> None:
    """Display the information message in a Textual TUI application.

    Args:
        message: The information message to display.
        driver: Driver callable that runs the application event loop. Defaults
            to ``_run_app`` (running ``app.run()``).

    Raises:
        TuiDisplayError: If Textual fails to run.
        KeyboardInterrupt: If the user interrupts the running application.
        SystemExit: If the application requests interpreter exit.
    """
    app = InfoApp(message)
    try:
        driver(app)
    except (KeyboardInterrupt, SystemExit):
        raise  # Let these propagate naturally
    except Exception as exc:
        msg = f"Failed to display TUI: {exc}"
        raise TuiDisplayError(msg) from exc


def main(*, show_tui: bool = True, driver: Callable[[InfoApp], None] = _run_app) -> int:
    """Entry point for the TUI script.

    Args:
        show_tui: When ``False``, write the info to stdout instead of starting
            the TUI (useful for headless environments and tests).
        driver: Optional driver callable for running the TUI app.

    Returns:
        int: ``0`` on success, ``1`` if the TUI could not be displayed.
    """
    info_message = build_info_message()
    logger.info("TUI entry point invoked. show_tui=%s", show_tui)

    if not show_tui:
        logger.info("TUI display skipped; writing info to stdout.")
        _ = sys.stdout.write(f"{info_message}\n")
        return 0

    try:
        _display_tui(info_message, driver=driver)
    except TuiDisplayError:
        logger.exception("Failed to display TUI; falling back to stdout.")
        _ = sys.stdout.write(f"{info_message}\n")
        return 1

    logger.info("TUI application closed successfully.")
    return 0
>>>>>>> after updating
