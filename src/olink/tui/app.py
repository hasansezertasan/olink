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
