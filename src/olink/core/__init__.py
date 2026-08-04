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
    "REGISTRY",
    "GitPageTarget",
    "MultiEcosystemTarget",
    "NoRemoteError",
    "NotGitRepoError",
    # Exceptions
    "OlinkError",
    "ProjectMetadataError",
    # Targets
    "Target",
    "UnknownPlatformError",
    "UnknownTargetError",
    "UnsupportedFeatureError",
    "get_target",
    "list_targets",
]
