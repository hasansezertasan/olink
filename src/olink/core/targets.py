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
    get_open_vsx_name,
    get_package_name,
    get_remote_url,
    parse_remote_url,
)


class Target(ABC):
    """Base class for all targets.

    Subclasses set `name` (CLI identifier) and `description` (help text), then
    implement `get_url(cwd)`. Implementations MUST raise OlinkError subclasses
    (NoRemoteError, ProjectMetadataError, UnsupportedFeatureError) rather than
    generic exceptions — CLI relies on the hierarchy for user-facing messages.
    """

    name: ClassVar[str]
    description: ClassVar[str]

    @abstractmethod
    def get_url(self, cwd: str) -> str:
        """Return the URL to open for this target, given a project directory.

        Args:
            cwd: Absolute path to the project root.

        Raises:
            OlinkError: Subclass appropriate to the failure (missing config,
                unsupported platform, etc.). Never a generic Exception.
        """


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
                    f"No supported ecosystem found for '{self.name}'. Supported: {available}"
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
PLATFORM_URLS: dict[str, dict[str, str | None]] = {
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
    # Gitea/Forgejo are GitHub-compatible — paths mirror github except no /security or /discussions
    "gitea": {
        "issues": "/issues",
        "pulls": "/pulls",
        "actions": "/actions",
        "wiki": "/wiki",
        "releases": "/releases",
        "branches": "/branches",
        "commits": "/commits",
        "security": None,
        "discussions": None,
    },
    "forgejo": {
        "issues": "/issues",
        "pulls": "/pulls",
        "actions": "/actions",
        "wiki": "/wiki",
        "releases": "/releases",
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
    """Open the remote origin URL.

    Reads .git/config; raises NotGitRepoError outside a repo, NoRemoteError
    if 'origin' is not configured.
    """

    name = "origin"
    description = "Open the remote origin URL"

    def get_url(self, cwd: str) -> str:
        return _get_parsed_remote(cwd, "origin").base_url


class UpstreamTarget(Target):
    """Open the upstream remote URL (fork workflows where origin = your fork).

    Raises NoRemoteError if 'upstream' remote is not configured.
    """

    name = "upstream"
    description = "Open the upstream remote URL"

    def get_url(self, cwd: str) -> str:
        return _get_parsed_remote(cwd, "upstream").base_url


class GitPageTarget(Target):
    """Base for targets that open a specific page on the git hosting platform.

    Subclasses set `_page` to a key in PLATFORM_URLS. Resolution raises
    UnsupportedFeatureError when the page is unavailable on the detected
    platform (e.g. discussions on GitLab).
    """

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
    """Open the Codecov page for the project.

    Codecov only integrates with GitHub, GitLab, and Bitbucket. Self-hosted
    forges (Gitea, Forgejo, Codeberg) are unsupported — raise rather than
    emit a 404 URL.
    """

    name = "codecov"
    description = "Open the Codecov page"

    _PLATFORM_CODES = {"github": "gh", "gitlab": "gl", "bitbucket": "bb"}

    def get_url(self, cwd: str) -> str:
        parsed = _get_parsed_remote(cwd, "origin")
        platform_code = self._PLATFORM_CODES.get(parsed.platform)
        if platform_code is None:
            raise UnsupportedFeatureError(
                f"Codecov does not support '{parsed.platform}' (only github, gitlab, bitbucket)"
            )
        return f"https://codecov.io/{platform_code}/{quote(parsed.owner, safe='')}/{quote(parsed.repo, safe='')}"


class CoverallsTarget(Target):
    """Open the Coveralls page for the project.

    Coveralls only integrates with GitHub, GitLab, and Bitbucket. Self-hosted
    forges (Gitea, Forgejo, Codeberg) are unsupported — raise rather than
    emit a 404 URL.
    """

    name = "coveralls"
    description = "Open the Coveralls page"

    _SUPPORTED_PLATFORMS = {"github", "gitlab", "bitbucket"}

    def get_url(self, cwd: str) -> str:
        parsed = _get_parsed_remote(cwd, "origin")
        if parsed.platform not in self._SUPPORTED_PLATFORMS:
            raise UnsupportedFeatureError(
                f"Coveralls does not support '{parsed.platform}' (only github, gitlab, bitbucket)"
            )
        return f"https://coveralls.io/{parsed.platform}/{quote(parsed.owner, safe='')}/{quote(parsed.repo, safe='')}"


# =============================================================================
# Python / PyPI Targets
# =============================================================================


class PyPITarget(Target):
    """Open the canonical PyPI project page. Requires pyproject.toml with [project].name."""

    name = "pypi"
    description = "Open the PyPI page"

    def get_url(self, cwd: str) -> str:
        return f"https://pypi.org/project/{_encode_name(get_package_name(cwd, 'pypi'))}/"


class InspectorTarget(Target):
    """Open PyPI Inspector (browse package source/files). Requires pyproject.toml."""

    name = "inspector"
    description = "Open the PyPI Inspector page"

    def get_url(self, cwd: str) -> str:
        return f"https://inspector.pypi.io/project/{_encode_name(get_package_name(cwd, 'pypi'))}/"


class PyPIJSONTarget(Target):
    """Open the JSON API endpoint for the package — useful for CI scripts and metadata checks."""

    name = "pypi-json"
    description = "Open the PyPI JSON API"

    def get_url(self, cwd: str) -> str:
        return f"https://pypi.org/pypi/{_encode_name(get_package_name(cwd, 'pypi'))}/json"


class PePyTarget(Target):
    """Open PePy.tech download stats. Requires pyproject.toml."""

    name = "pepy"
    description = "Open the PePy download stats"

    def get_url(self, cwd: str) -> str:
        return f"https://www.pepy.tech/projects/{_encode_name(get_package_name(cwd, 'pypi'))}"


class PyPIStatsTarget(Target):
    """Open pypistats.org download charts. Requires pyproject.toml."""

    name = "pypistats"
    description = "Open the PyPI Stats page"

    def get_url(self, cwd: str) -> str:
        return f"https://pypistats.org/packages/{_encode_name(get_package_name(cwd, 'pypi'))}"


class PiWheelsTarget(Target):
    """Expose piwheels so Python projects can validate Raspberry Pi package availability."""

    name = "piwheels"
    description = "Open the piwheels project page"

    def get_url(self, cwd: str) -> str:
        """Reuse PyPI metadata lookup so package naming stays consistent across Python targets."""
        return f"https://www.piwheels.org/project/{_encode_name(get_package_name(cwd, 'pypi'))}/"


class PipTrendsTarget(Target):
    """Open piptrends.com download trends. Requires pyproject.toml."""

    name = "piptrends"
    description = "Open the Pip Trends page"

    def get_url(self, cwd: str) -> str:
        return f"https://piptrends.com/package/{_encode_name(get_package_name(cwd, 'pypi'))}"


class ClickPyTarget(Target):
    """Open ClickPy ClickHouse-backed stats dashboard. Requires pyproject.toml."""

    name = "clickpy"
    description = "Open the ClickPy stats (ClickHouse)"

    def get_url(self, cwd: str) -> str:
        return f"https://clickpy.clickhouse.com/dashboard/{_encode_name(get_package_name(cwd, 'pypi'))}"


class SafetyDBTarget(Target):
    """Open Safety DB vulnerability page for the PyPI package. Requires pyproject.toml."""

    name = "safety-db"
    description = "Open the Safety DB page"

    def get_url(self, cwd: str) -> str:
        return f"https://data.safetycli.com/packages/pypi/{_encode_name(get_package_name(cwd, 'pypi'))}"


# =============================================================================
# Multi-Ecosystem Targets
# =============================================================================


class SnykTarget(MultiEcosystemTarget):
    """Snyk security advisor. Snyk uses non-obvious slugs (npm-package, golang, rust)."""

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
    """Libraries.io aggregate package page. Slugs match ecosystem keys 1:1."""

    name = "libraries-io"
    description = "Open the Libraries.io page"
    ecosystem_url_map = {"pypi": "pypi", "npm": "npm", "cargo": "cargo", "go": "go"}

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        return f"https://libraries.io/{ecosystem_path}/{_encode_name(package_name)}"


class DepsDevTarget(MultiEcosystemTarget):
    """Google deps.dev — dependency graph and security info."""

    name = "deps"
    description = "Open deps.dev (Google Open Source Insights)"
    ecosystem_url_map = {"pypi": "pypi", "npm": "npm", "cargo": "cargo", "go": "go"}

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        return f"https://deps.dev/{ecosystem_path}/{_encode_name(package_name)}"


class EcosystemsTarget(MultiEcosystemTarget):
    """ecosyste.ms registry index. Uses host-style ecosystem slugs (pypi.org, npmjs.org)."""

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


class SocketTarget(MultiEcosystemTarget):
    """Expose Socket.dev package risk pages across major ecosystems from one target."""

    name = "socket"
    description = "Open Socket.dev package health"
    ecosystem_url_map = {
        "pypi": "pypi",
        "npm": "npm",
        "cargo": "cargo",
        "go": "go",
    }

    def _build_url(self, ecosystem_path: str, package_name: str) -> str:
        """Encode package names safely because Socket URLs include the raw package identifier."""
        return f"https://socket.dev/{ecosystem_path}/package/{_encode_name(package_name)}"


# =============================================================================
# npm Targets
# =============================================================================


class NPMTarget(Target):
    """Open npmjs.com package page. Handles scoped names (@org/pkg) via _encode_name."""

    name = "npm"
    description = "Open the npm page"

    def get_url(self, cwd: str) -> str:
        return f"https://www.npmjs.com/package/{_encode_name(get_package_name(cwd, 'npm'))}"


class BundlephobiaTarget(Target):
    """Open Bundlephobia (browser bundle size analyzer). Requires package.json."""

    name = "bundlephobia"
    description = "Open Bundlephobia (bundle size)"

    def get_url(self, cwd: str) -> str:
        return f"https://bundlephobia.com/package/{_encode_name(get_package_name(cwd, 'npm'))}"


class PackagephobiaTarget(Target):
    """Open Packagephobia (install size). Uses ?p=<name> query — urlencode handles scoped names."""

    name = "packagephobia"
    description = "Open Packagephobia (install size)"

    def get_url(self, cwd: str) -> str:
        return "https://packagephobia.com/result?" + urlencode({"p": get_package_name(cwd, "npm")})


class NPMStatTarget(Target):
    """Open npm-stat download charts. Uses ?package=<name> query string."""

    name = "npm-stat"
    description = "Open npm-stat download charts"

    def get_url(self, cwd: str) -> str:
        return "https://npm-stat.com/charts.html?" + urlencode(
            {"package": get_package_name(cwd, "npm")}
        )


class JsDelivrTarget(Target):
    """Shortcut CDN package inspection for frontend dependency debugging workflows."""

    name = "jsdelivr"
    description = "Open jsDelivr package page"

    def get_url(self, cwd: str) -> str:
        """Reuse npm package metadata so scoped names remain valid without extra mapping rules."""
        return f"https://www.jsdelivr.com/package/npm/{_encode_name(get_package_name(cwd, 'npm'))}"


class UnpkgTarget(Target):
    """Give maintainers a direct view of published npm artifacts as served by UNPKG."""

    name = "unpkg"
    description = "Open the UNPKG package page"

    def get_url(self, cwd: str) -> str:
        """Use the package name from package.json so URL previews match published package IDs."""
        return f"https://unpkg.com/{_encode_name(get_package_name(cwd, 'npm'))}"


class SkypackTarget(Target):
    """Support quick compatibility checks against Skypack's ESM package view."""

    name = "skypack"
    description = "Open the Skypack package page"

    def get_url(self, cwd: str) -> str:
        """Derive URLs from npm metadata to keep behavior aligned with other JavaScript targets."""
        return f"https://www.skypack.dev/view/{_encode_name(get_package_name(cwd, 'npm'))}"


# =============================================================================
# Rust / Crates Targets
# =============================================================================


class CratesTarget(Target):
    """Open crates.io crate page. Requires Cargo.toml with [package].name."""

    name = "crates"
    description = "Open the crates.io page"

    def get_url(self, cwd: str) -> str:
        return f"https://crates.io/crates/{_encode_name(get_package_name(cwd, 'cargo'))}"


class LibRsTarget(Target):
    """Open lib.rs (alternative crates.io browser, faster UX). Requires Cargo.toml."""

    name = "librs"
    description = "Open lib.rs (alternative crates browser)"

    def get_url(self, cwd: str) -> str:
        return f"https://lib.rs/crates/{_encode_name(get_package_name(cwd, 'cargo'))}"


class DocsRsTarget(Target):
    """Expose docs.rs so Rust users can jump directly to hosted API docs."""

    name = "docsrs"
    description = "Open docs.rs API documentation"

    def get_url(self, cwd: str) -> str:
        """Reuse Cargo metadata extraction to keep Rust naming logic consistent."""
        return f"https://docs.rs/{_encode_name(get_package_name(cwd, 'cargo'))}"


# =============================================================================
# Go Targets
# =============================================================================


class GoPkgTarget(Target):
    """Expose pkg.go.dev so Go maintainers can inspect published module docs."""

    name = "pkg-go"
    description = "Open pkg.go.dev module page"

    def get_url(self, cwd: str) -> str:
        """Link to the canonical Go package index used by most ecosystem tooling."""
        return f"https://pkg.go.dev/{_encode_name(get_package_name(cwd, 'go'))}"


class GoDocsTarget(Target):
    """Provide an intuitive alias for Go users who look for docs-oriented target names."""

    name = "go-docs"
    description = "Open pkg.go.dev documentation"

    def get_url(self, cwd: str) -> str:
        """Reuse go.mod module lookup so docs links match the canonical module identifier."""
        return f"https://pkg.go.dev/{_encode_name(get_package_name(cwd, 'go'))}"


# =============================================================================
# Ruby Targets
# =============================================================================


class GemsTarget(Target):
    """Open rubygems.org gem page. Requires *.gemspec with `spec.name = "..."`."""

    name = "gems"
    description = "Open the RubyGems page"

    def get_url(self, cwd: str) -> str:
        return f"https://rubygems.org/gems/{_encode_name(get_package_name(cwd, 'gems'))}"


class RubyGemsStatsTarget(Target):
    """Expose RubyGems usage stats to help maintainers gauge adoption quickly."""

    name = "rubygems-stats"
    description = "Open RubyGems download stats"

    def get_url(self, cwd: str) -> str:
        """Build on gemspec name extraction so package identity stays consistent across Ruby targets."""
        return f"https://rubygems.org/gems/{_encode_name(get_package_name(cwd, 'gems'))}/stats"


# =============================================================================
# PHP Targets
# =============================================================================


class PackagistTarget(Target):
    """Open Packagist PHP package page. Composer name format vendor/package preserved."""

    name = "packagist"
    description = "Open the Packagist page (PHP)"

    def get_url(self, cwd: str) -> str:
        return f"https://packagist.org/packages/{_encode_name(get_package_name(cwd, 'packagist'))}"


# =============================================================================
# Dart / Flutter Targets
# =============================================================================


class PubTarget(Target):
    """Open pub.dev (Dart/Flutter) package page. Requires pubspec.yaml."""

    name = "pub"
    description = "Open the pub.dev page (Dart/Flutter)"

    def get_url(self, cwd: str) -> str:
        return f"https://pub.dev/packages/{_encode_name(get_package_name(cwd, 'pub'))}"


# =============================================================================
# Elixir Targets
# =============================================================================


class HexTarget(Target):
    """Open hex.pm (Elixir) package page. Uses OTP `app:` atom from mix.exs."""

    name = "hex"
    description = "Open the hex.pm page (Elixir)"

    def get_url(self, cwd: str) -> str:
        return f"https://hex.pm/packages/{_encode_name(get_package_name(cwd, 'hex'))}"


# =============================================================================
# .NET Targets
# =============================================================================


class NuGetTarget(Target):
    """Open NuGet (.NET) package page. Falls back to *.csproj filename when <PackageId> absent."""

    name = "nuget"
    description = "Open the NuGet page (.NET)"

    def get_url(self, cwd: str) -> str:
        return f"https://www.nuget.org/packages/{_encode_name(get_package_name(cwd, 'nuget'))}"


class OpenVSXTarget(Target):
    """Enable extension authors to jump from local metadata straight to Open VSX listings."""

    name = "open-vsx"
    description = "Open the Open VSX extension page"

    def get_url(self, cwd: str) -> str:
        """Use publisher + name from package.json because Open VSX identifies extensions by both."""
        publisher_name = get_open_vsx_name(cwd)
        if "." not in publisher_name:
            raise ProjectMetadataError(
                f"Invalid Open VSX identifier '{publisher_name}': "
                "expected 'publisher.name' format in package.json"
            )
        publisher, name = publisher_name.split(".", 1)
        return f"https://open-vsx.org/extension/{_encode_name(publisher)}/{_encode_name(name)}"


class MavenTarget(Target):
    """Expose Maven Central pages for JVM artifacts based on standard project coordinates."""

    name = "maven"
    description = "Open the Maven Central artifact page"

    def get_url(self, cwd: str) -> str:
        """Convert groupId/artifactId coordinates into Maven Central's artifact URL format."""
        group_artifact = get_package_name(cwd, "maven")
        if ":" not in group_artifact:
            raise ProjectMetadataError(
                f"Invalid Maven coordinates '{group_artifact}': "
                "expected 'groupId:artifactId' format from pom.xml"
            )
        group_id, artifact_id = group_artifact.split(":", 1)
        return f"https://central.sonatype.com/artifact/{_encode_name(group_id)}/{_encode_name(artifact_id)}"


class HackageTarget(Target):
    """Help Haskell maintainers inspect package metadata directly on Hackage."""

    name = "hackage"
    description = "Open the Hackage package page"

    def get_url(self, cwd: str) -> str:
        """Reuse cabal package naming to avoid introducing Haskell-specific URL translation logic."""
        return (
            f"https://hackage.haskell.org/package/{_encode_name(get_package_name(cwd, 'hackage'))}"
        )


class CpanTarget(Target):
    """Surface MetaCPAN lookup for Perl dependencies from lightweight cpanfile metadata."""

    name = "cpan"
    description = "Open the MetaCPAN module page"

    def get_url(self, cwd: str) -> str:
        """Map the module name directly to MetaCPAN for immediate documentation and release access."""
        return f"https://metacpan.org/pod/{_encode_name(get_package_name(cwd, 'cpan'))}"
