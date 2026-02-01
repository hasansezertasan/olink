"""Core functionality for olink."""

from olink.core.catalog import REGISTRY, get_target, list_targets
from olink.core.exceptions import (
    NoRemoteError,
    NotGitRepoError,
    OlinkError,
    ProjectMetadataError,
    UnknownPlatformError,
    UnknownTargetError,
    UnsupportedFeatureError,
)
from olink.core.targets import GitPageTarget, MultiEcosystemTarget, Target

__all__ = [
    # Targets
    "Target",
    "GitPageTarget",
    "MultiEcosystemTarget",
    "REGISTRY",
    "get_target",
    "list_targets",
    # Exceptions
    "OlinkError",
    "NotGitRepoError",
    "NoRemoteError",
    "UnknownPlatformError",
    "UnknownTargetError",
    "ProjectMetadataError",
    "UnsupportedFeatureError",
]
