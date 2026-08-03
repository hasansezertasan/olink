"""Data models for the TUI."""

from dataclasses import dataclass

from olink.core.catalog import REGISTRY, list_available_targets
from olink.core.targets import MultiEcosystemTarget, Target


@dataclass
class TargetItem:
    """A target entry for display in the TUI."""

    name: str
    description: str
    target_cls: type[Target]
    ecosystem: str | None = None
    pinned: bool = False

    def get_url(self, cwd: str) -> str:
        """Resolve the URL for this target."""
        if self.ecosystem and issubclass(self.target_cls, MultiEcosystemTarget):
            return self.target_cls(ecosystem=self.ecosystem).get_url(cwd)
        return self.target_cls().get_url(cwd)


@dataclass
class FilterState:
    """Current TUI filter/view state."""

    mode: str = "available"  # "all" or "available"


def build_all_targets() -> list[TargetItem]:
    """Build list of all registered targets."""
    return [
        TargetItem(name=name, description=target_cls.description, target_cls=target_cls)
        for name, target_cls in sorted(REGISTRY.items())
    ]


def build_available_targets(cwd: str) -> list[TargetItem]:
    """Build list of targets available for the current project."""
    return [
        TargetItem(name=name, description=desc, target_cls=cls, ecosystem=eco)
        for name, desc, cls, eco in list_available_targets(cwd)
    ]


def order_by_pins(items: list[TargetItem], pinned: list[str]) -> list[TargetItem]:
    """Return items pinned-first, marking each item's `pinned` flag.

    Pinned items come first in the order they appear in `pinned`; the rest keep
    their incoming order. Pin names absent from `items` are ignored, so in the
    TUI's "available" mode a pin only surfaces when it applies to this project.
    """
    rank = {name: index for index, name in enumerate(pinned)}
    for item in items:
        item.pinned = item.name in rank
    pinned_items = sorted(
        (item for item in items if item.pinned),
        key=lambda item: rank[item.name],
    )
    rest = [item for item in items if not item.pinned]
    return [*pinned_items, *rest]
