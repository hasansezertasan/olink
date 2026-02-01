"""Custom exceptions for olink."""


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
