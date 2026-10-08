"""Custom exceptions for olink."""

__all__ = [
    "InvalidDirectoryError",
    "NoRemoteError",
    "NotGitRepoError",
    "OlinkError",
    "ProjectMetadataError",
    "UnknownPlatformError",
    "UnknownTargetError",
    "UnsupportedFeatureError",
]


class OlinkError(Exception):
    """Base exception for olink."""


class NotGitRepoError(OlinkError):
    """Not inside a git repository."""


class NoRemoteError(OlinkError):
    """No git remote configured."""


class UnknownPlatformError(OlinkError):
    """Unknown git hosting platform."""


class UnknownTargetError(OlinkError):
    """Unknown target specified."""


class ProjectMetadataError(OlinkError):
    """Could not read project metadata."""


class UnsupportedFeatureError(OlinkError):
    """Feature not available on this platform."""


class InvalidDirectoryError(OlinkError):
    """Project directory is missing or is not a directory."""
