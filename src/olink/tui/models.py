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
