"""All target definitions."""

from abc import ABC, abstractmethod
from typing import ClassVar
from urllib.parse import quote, urlencode

from olink.core.exceptions import (
    NoRemoteError,
    ProjectMetadataError,
    UnknownPlatformError,
    UnsupportedFeatureError,
)
from olink.core.project import (
    ParsedRemote,
    detect_ecosystems,
    get_package_name,
    get_remote_url,
    parse_remote_url,
)


class Target(ABC):
    """Base class for all targets."""

    name: ClassVar[str]
    description: ClassVar[str]

    @abstractmethod
    def get_url(self, cwd: str) -> str:
        """Return the URL to open."""


class MultiEcosystemTarget(Target):
    """Base class for targets that support multiple ecosystems.

    Supports suffix notation: target:ecosystem
    e.g., snyk:pypi, deps:npm, libraries-io:cargo
    """

    name: ClassVar[str]
    description: ClassVar[str]
    ecosystem_url_map: ClassVar[dict[str, str]]

    def __init__(self, ecosystem: str | None = None):
        self._ecosystem = ecosystem

    @abstractmethod
    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        """Build the URL for the given ecosystem and package."""

    def get_url(self, cwd: str) -> str:
        """Get the URL, auto-detecting ecosystem if not specified."""

        if self._ecosystem:
            if self._ecosystem not in self.ecosystem_url_map:
                available = ", ".join(sorted(self.ecosystem_url_map.keys()))
                raise ProjectMetadataError(
                    f"'{self.name}' doesn't support ecosystem '{self._ecosystem}'. "
                    f"Supported: {available}"
                )
            ecosystem = self._ecosystem
        else:
            detected = detect_ecosystems(cwd)
            supported = [e for e in detected if e in self.ecosystem_url_map]

            if not supported:
                available = ", ".join(sorted(self.ecosystem_url_map.keys()))
                raise ProjectMetadataError(
                    f"No supported ecosystem found for '{self.name}'. "
                    f"Supported: {available}"
                )

            if len(supported) > 1:
                variants = ", ".join(f"{self.name}:{e}" for e in sorted(supported))
                raise ProjectMetadataError(
                    f"Multiple ecosystems detected ({', '.join(sorted(supported))}). "
                    f"Use: {variants}"
                )

            ecosystem = supported[0]

        package_name = get_package_name(cwd, ecosystem)
        ecosystem_path = self.ecosystem_url_map[ecosystem]
        return self._build_url(ecosystem_path, package_name)


def _encode_name(name: str) -> str:
    """URL-encode a package name, preserving @ and / for scoped npm packages."""
    return quote(name, safe="@/")


# =============================================================================
# Git Targets
# =============================================================================

# Platform URL patterns: {platform: {page: path_suffix}}
# None means the feature is not available on that platform
PLATFORM_URLS = {
    "github": {
        "issues": "/issues",
        "pulls": "/pulls",
        "actions": "/actions",
        "wiki": "/wiki",
        "releases": "/releases",
        "branches": "/branches",
        "commits": "/commits",
        "security": "/security",
        "discussions": "/discussions",
    },
    "gitlab": {
        "issues": "/-/issues",
        "pulls": "/-/merge_requests",
        "actions": "/-/pipelines",
        "wiki": "/-/wikis",
        "releases": "/-/releases",
        "branches": "/-/branches",
        "commits": "/-/commits",
        "security": "/-/security/dashboard",
        "discussions": None,
    },
    "bitbucket": {
        "issues": "/issues",
        "pulls": "/pull-requests",
        "actions": "/pipelines",
        "wiki": "/wiki",
        "releases": "/downloads",
        "branches": "/branches",
        "commits": "/commits",
        "security": None,
        "discussions": None,
    },
}


def _get_parsed_remote(cwd: str, remote: str = "origin") -> ParsedRemote:
    """Get and parse a git remote, raising NoRemoteError if missing."""
    remote_url = get_remote_url(cwd, remote)
    if not remote_url:
        raise NoRemoteError(f"No '{remote}' remote configured")
    return parse_remote_url(remote_url)


def get_platform_url(base_url: str, platform: str, page: str) -> str:
    """Get URL for a specific page on a platform."""
    if platform not in PLATFORM_URLS:
        raise UnknownPlatformError(f"Unknown platform: '{platform}'")
    if page not in PLATFORM_URLS[platform]:
        available = ", ".join(sorted(PLATFORM_URLS[platform].keys()))
        raise UnsupportedFeatureError(
            f"Unknown page '{page}' for {platform}. Available: {available}"
        )
    path = PLATFORM_URLS[platform][page]
    if path is None:
        raise UnsupportedFeatureError(f"'{page}' is not available on {platform}")
    return base_url + path


class OriginTarget(Target):
    """Open the remote origin URL."""

    name = "origin"
    description = "Open the remote origin URL"

    def get_url(self, cwd: str) -> str:
        return _get_parsed_remote(cwd, "origin").base_url


class UpstreamTarget(Target):
    """Open the upstream remote URL."""

    name = "upstream"
    description = "Open the upstream remote URL"

    def get_url(self, cwd: str) -> str:
        return _get_parsed_remote(cwd, "upstream").base_url


class GitPageTarget(Target):
    """Base for targets that open a specific page on the git hosting platform."""

    _page: str

    def get_url(self, cwd: str) -> str:
        parsed = _get_parsed_remote(cwd, "origin")
        return get_platform_url(parsed.base_url, parsed.platform, self._page)


class IssuesTarget(GitPageTarget):
    name = "issues"
    description = "Open the issues page"
    _page = "issues"


class PullsTarget(GitPageTarget):
    name = "pulls"
    description = "Open the pull/merge requests page"
    _page = "pulls"


class ActionsTarget(GitPageTarget):
    name = "actions"
    description = "Open the CI/CD page (Actions, Pipelines)"
    _page = "actions"


class WikiTarget(GitPageTarget):
    name = "wiki"
    description = "Open the wiki page"
    _page = "wiki"


class ReleasesTarget(GitPageTarget):
    name = "releases"
    description = "Open the releases page"
    _page = "releases"


class BranchesTarget(GitPageTarget):
    name = "branches"
    description = "Open the branches page"
    _page = "branches"


class CommitsTarget(GitPageTarget):
    name = "commits"
    description = "Open the commit history"
    _page = "commits"


class SecurityTarget(GitPageTarget):
    name = "security"
    description = "Open the security page"
    _page = "security"


class DiscussionsTarget(GitPageTarget):
    name = "discussions"
    description = "Open the discussions page"
    _page = "discussions"


# =============================================================================
# Service Targets (git-remote based)
# =============================================================================


class CodecovTarget(Target):
    """Open the Codecov page for the project."""

    name = "codecov"
    description = "Open the Codecov page"

    _PLATFORM_CODES = {"github": "gh", "gitlab": "gl", "bitbucket": "bb"}

    def get_url(self, cwd: str) -> str:
        parsed = _get_parsed_remote(cwd, "origin")
        platform_code = self._PLATFORM_CODES.get(parsed.platform, parsed.platform)
        return f"https://codecov.io/{platform_code}/{quote(parsed.owner, safe='')}/{quote(parsed.repo, safe='')}"


class CoverallsTarget(Target):
    """Open the Coveralls page for the project."""

    name = "coveralls"
    description = "Open the Coveralls page"

    def get_url(self, cwd: str) -> str:
        parsed = _get_parsed_remote(cwd, "origin")
        return f"https://coveralls.io/{parsed.platform}/{quote(parsed.owner, safe='')}/{quote(parsed.repo, safe='')}"


# =============================================================================
# Python / PyPI Targets
# =============================================================================


class PyPITarget(Target):
    name = "pypi"
    description = "Open the PyPI page"

    def get_url(self, cwd: str) -> str:
        return (
            f"https://pypi.org/project/{_encode_name(get_package_name(cwd, 'pypi'))}/"
        )


class InspectorTarget(Target):
    name = "inspector"
    description = "Open the PyPI Inspector page"

    def get_url(self, cwd: str) -> str:
        return f"https://inspector.pypi.io/project/{_encode_name(get_package_name(cwd, 'pypi'))}/"


class PyPIJSONTarget(Target):
    name = "pypi-json"
    description = "Open the PyPI JSON API"

    def get_url(self, cwd: str) -> str:
        return (
            f"https://pypi.org/pypi/{_encode_name(get_package_name(cwd, 'pypi'))}/json"
        )


class PePyTarget(Target):
    name = "pepy"
    description = "Open the PePy download stats"

    def get_url(self, cwd: str) -> str:
        return f"https://www.pepy.tech/projects/{_encode_name(get_package_name(cwd, 'pypi'))}"


class PyPIStatsTarget(Target):
    name = "pypistats"
    description = "Open the PyPI Stats page"

    def get_url(self, cwd: str) -> str:
        return f"https://pypistats.org/packages/{_encode_name(get_package_name(cwd, 'pypi'))}"


class PiWheelsTarget(Target):
    """Provide quick access to piwheels when validating Raspberry Pi builds."""

    name = "piwheels"
    description = "Open the piwheels project page"

    def get_url(self, cwd: str) -> str:
        """Mirror Python target behavior so one project config powers multiple registries."""
        return f"https://www.piwheels.org/project/{_encode_name(get_package_name(cwd, 'pypi'))}/"


class PipTrendsTarget(Target):
    name = "piptrends"
    description = "Open the Pip Trends page"

    def get_url(self, cwd: str) -> str:
        return f"https://piptrends.com/package/{_encode_name(get_package_name(cwd, 'pypi'))}"


class ClickPyTarget(Target):
    name = "clickpy"
    description = "Open the ClickPy stats (ClickHouse)"

    def get_url(self, cwd: str) -> str:
        return f"https://clickpy.clickhouse.com/dashboard/{_encode_name(get_package_name(cwd, 'pypi'))}"


class SafetyDBTarget(Target):
    name = "safety-db"
    description = "Open the Safety DB page"

    def get_url(self, cwd: str) -> str:
        return f"https://data.safetycli.com/packages/pypi/{_encode_name(get_package_name(cwd, 'pypi'))}"


# =============================================================================
# Multi-Ecosystem Targets
# =============================================================================


class SnykTarget(MultiEcosystemTarget):
    name = "snyk"
    description = "Open the Snyk security advisor"
    ecosystem_url_map = {
        "pypi": "python",
        "npm": "npm-package",
        "go": "golang",
        "cargo": "rust",
    }

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        return f"https://snyk.io/advisor/{ecosystem_path}/{_encode_name(package_name)}"


class LibrariesIOTarget(MultiEcosystemTarget):
    name = "libraries-io"
    description = "Open the Libraries.io page"
    ecosystem_url_map = {"pypi": "pypi", "npm": "npm", "cargo": "cargo", "go": "go"}

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        return f"https://libraries.io/{ecosystem_path}/{_encode_name(package_name)}"


class DepsDevTarget(MultiEcosystemTarget):
    name = "deps"
    description = "Open deps.dev (Google Open Source Insights)"
    ecosystem_url_map = {"pypi": "pypi", "npm": "npm", "cargo": "cargo", "go": "go"}

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        return f"https://deps.dev/{ecosystem_path}/{_encode_name(package_name)}"


class EcosystemsTarget(MultiEcosystemTarget):
    name = "ecosystems"
    description = "Open the ecosyste.ms page"
    ecosystem_url_map = {
        "pypi": "pypi.org",
        "npm": "npmjs.org",
        "cargo": "crates.io",
        "go": "proxy.golang.org",
    }

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        return f"https://packages.ecosyste.ms/registries/{ecosystem_path}/packages/{_encode_name(package_name)}"


# =============================================================================
# npm Targets
# =============================================================================


class NPMTarget(Target):
    name = "npm"
    description = "Open the npm page"

    def get_url(self, cwd: str) -> str:
        return f"https://www.npmjs.com/package/{_encode_name(get_package_name(cwd, 'npm'))}"


class BundlephobiaTarget(Target):
    name = "bundlephobia"
    description = "Open Bundlephobia (bundle size)"

    def get_url(self, cwd: str) -> str:
        return f"https://bundlephobia.com/package/{_encode_name(get_package_name(cwd, 'npm'))}"


class PackagephobiaTarget(Target):
    name = "packagephobia"
    description = "Open Packagephobia (install size)"

    def get_url(self, cwd: str) -> str:
        return "https://packagephobia.com/result?" + urlencode(
            {"p": get_package_name(cwd, "npm")}
        )


class NPMStatTarget(Target):
    name = "npm-stat"
    description = "Open npm-stat download charts"

    def get_url(self, cwd: str) -> str:
        return "https://npm-stat.com/charts.html?" + urlencode(
            {"package": get_package_name(cwd, "npm")}
        )


# =============================================================================
# Rust / Crates Targets
# =============================================================================


class CratesTarget(Target):
    name = "crates"
    description = "Open the crates.io page"

    def get_url(self, cwd: str) -> str:
        return (
            f"https://crates.io/crates/{_encode_name(get_package_name(cwd, 'cargo'))}"
        )


class LibRsTarget(Target):
    name = "librs"
    description = "Open lib.rs (alternative crates browser)"

    def get_url(self, cwd: str) -> str:
        return f"https://lib.rs/crates/{_encode_name(get_package_name(cwd, 'cargo'))}"


# =============================================================================
# Ruby Targets
# =============================================================================


class GemsTarget(Target):
    name = "gems"
    description = "Open the RubyGems page"

    def get_url(self, cwd: str) -> str:
        return (
            f"https://rubygems.org/gems/{_encode_name(get_package_name(cwd, 'gems'))}"
        )


# =============================================================================
# PHP Targets
# =============================================================================


class PackagistTarget(Target):
    name = "packagist"
    description = "Open the Packagist page (PHP)"

    def get_url(self, cwd: str) -> str:
        return f"https://packagist.org/packages/{_encode_name(get_package_name(cwd, 'packagist'))}"


# =============================================================================
# Dart / Flutter Targets
# =============================================================================


class PubTarget(Target):
    name = "pub"
    description = "Open the pub.dev page (Dart/Flutter)"

    def get_url(self, cwd: str) -> str:
        return f"https://pub.dev/packages/{_encode_name(get_package_name(cwd, 'pub'))}"


# =============================================================================
# Elixir Targets
# =============================================================================


class HexTarget(Target):
    name = "hex"
    description = "Open the hex.pm page (Elixir)"

    def get_url(self, cwd: str) -> str:
        return f"https://hex.pm/packages/{_encode_name(get_package_name(cwd, 'hex'))}"


# =============================================================================
# .NET Targets
# =============================================================================


class NuGetTarget(Target):
    name = "nuget"
    description = "Open the NuGet page (.NET)"

    def get_url(self, cwd: str) -> str:
        return f"https://www.nuget.org/packages/{_encode_name(get_package_name(cwd, 'nuget'))}"
