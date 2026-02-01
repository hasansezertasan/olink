"""Custom Textual widgets for the TUI."""

from rich.text import Text
from textual.widgets import ListItem, ListView, Static

from olink.tui.models import TargetItem


class TargetRow(ListItem):
    """A single target row in the list."""

    def __init__(self, item: TargetItem) -> None:
        self.item = item
        super().__init__()

    def compose(self):  # noqa: ANN201
        label = Text()
        label.append(f" {self.item.name:20s}", style="cyan")
        label.append(f" {self.item.description}")
        yield Static(label)


class TargetListWidget(ListView):
    """Scrollable list of targets."""

    def __init__(self) -> None:
        super().__init__()

    def get_selected_item(self) -> TargetItem | None:
        """Get the currently highlighted target item."""
        if self.highlighted_child is not None:
            assert isinstance(self.highlighted_child, TargetRow)
            return self.highlighted_child.item
        return None

    def update_items(self, items: list[TargetItem]) -> None:
        """Replace the list contents."""
        self.clear()
        for item in items:
            self.append(TargetRow(item))


class StatusBar(Static):
    """Bottom status bar showing mode, count, and messages."""

    def on_mount(self) -> None:
        self.styles.background = "darkblue"
        self.styles.color = "white"
        self.styles.height = 1
        self.styles.dock = "bottom"

    def status_update(self, mode: str, count: int, total: int) -> None:
        """Update the status bar content."""
        mode_label = "Available" if mode == "available" else "All"
        self.update(f" [{mode_label}: {count}/{total}]")
        self.styles.color = "white"

    def set_error(self, message: str) -> None:
        """Show an error message."""
        self.update(f" \u2717 {message}")
        self.styles.color = "red"

    def set_success(self, message: str) -> None:
        """Show a success message."""
        self.update(f" \u2713 {message}")
        self.styles.color = "green"
