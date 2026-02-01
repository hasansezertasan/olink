"""Main TUI application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from olink.core.exceptions import OlinkError
from olink.tui.actions import copy_to_clipboard, open_in_browser
from olink.tui.models import (
    FilterState,
    TargetItem,
    build_all_targets,
    build_available_targets,
)
from olink.tui.widgets import StatusBar, TargetListWidget

HEADER_TEXT = (
    "olink — Interactive Target Browser\nTab: toggle view  o: open  c: copy  q: quit"
)


class OlinkTUI(App):
    """Main TUI application managing state and widget composition."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "toggle_mode", "Toggle view", priority=True),
        Binding("o", "open_target", "Open"),
        Binding("c", "copy_target", "Copy"),
    ]

    def __init__(self, cwd: str) -> None:
        super().__init__()
        self.cwd = cwd
        self.state = FilterState()
        self.all_targets = build_all_targets()
        self.available_targets = build_available_targets(cwd)

    def compose(self) -> ComposeResult:
        header = Static(HEADER_TEXT, id="header")
        header.styles.background = "darkblue"
        header.styles.color = "white"
        header.styles.text_style = "bold"
        header.styles.dock = "top"
        header.styles.height = 2
        yield header
        yield TargetListWidget()
        yield StatusBar()

    def on_mount(self) -> None:
        self._refresh_list()

    def _source(self) -> list[TargetItem]:
        return (
            self.available_targets
            if self.state.mode == "available"
            else self.all_targets
        )

    def _refresh_list(self) -> None:
        self.query_one(TargetListWidget).update_items(self._source())
        self._refresh_status()

    def _refresh_status(self) -> None:
        count = len(self._source())
        total = len(self.all_targets)
        self.query_one(StatusBar).status_update(self.state.mode, count, total)

    def action_toggle_mode(self) -> None:
        self.state.mode = "all" if self.state.mode == "available" else "available"
        self._refresh_list()

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


def launch_tui(cwd: str) -> None:
    """Entry point for the TUI."""
    OlinkTUI(cwd).run()
