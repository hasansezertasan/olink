"""Data models for the TUI."""

import logging
from dataclasses import dataclass

from olink.core.exceptions import (
    NoRemoteError,
    NotGitRepoError,
    ProjectMetadataError,
    UnsupportedFeatureError,
)
from olink.core.catalog import REGISTRY
from olink.core.targets import MultiEcosystemTarget, Target

logger = logging.getLogger(__name__)

_UNAVAILABLE_ERRORS = (NoRemoteError, NotGitRepoError, ProjectMetadataError, UnsupportedFeatureError)


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
    from olink.core.project import detect_ecosystems

    items: list[TargetItem] = []
    detected_ecosystems = detect_ecosystems(cwd)

    for name, target_cls in sorted(REGISTRY.items()):
        if issubclass(target_cls, MultiEcosystemTarget):
            supported = [
                e for e in detected_ecosystems if e in target_cls.ecosystem_url_map
            ]
            if not supported:
                continue
            if len(supported) == 1:
                try:
                    target_cls(ecosystem=supported[0]).get_url(cwd)
                    items.append(
                        TargetItem(
                            name=name,
                            description=f"{target_cls.description} ({supported[0]})",
                            target_cls=target_cls,
                            ecosystem=supported[0],
                        )
                    )
                except _UNAVAILABLE_ERRORS as e:
                    logger.debug("Skipping %s: %s", name, e)
            else:
                for eco in sorted(supported):
                    try:
                        target_cls(ecosystem=eco).get_url(cwd)
                        items.append(
                            TargetItem(
                                name=f"{name}:{eco}",
                                description=target_cls.description,
                                target_cls=target_cls,
                                ecosystem=eco,
                            )
                        )
                    except _UNAVAILABLE_ERRORS as e:
                        logger.debug("Skipping %s:%s: %s", name, eco, e)
        else:
            try:
                target_cls().get_url(cwd)
                items.append(
                    TargetItem(
                        name=name,
                        description=target_cls.description,
                        target_cls=target_cls,
                    )
                )
            except _UNAVAILABLE_ERRORS as e:
                logger.debug("Skipping %s: %s", name, e)
    return items
