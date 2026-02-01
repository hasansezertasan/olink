"""Target catalog - explicit registration of all targets."""

from olink.core.exceptions import UnknownTargetError
from olink.core.targets import (
    # Git targets
    OriginTarget,
    UpstreamTarget,
    IssuesTarget,
    PullsTarget,
    ActionsTarget,
    WikiTarget,
    ReleasesTarget,
    BranchesTarget,
    CommitsTarget,
    SecurityTarget,
    DiscussionsTarget,
    # Service targets
    CodecovTarget,
    CoverallsTarget,
    # Python / PyPI
    PyPITarget,
    InspectorTarget,
    PyPIJSONTarget,
    PePyTarget,
    PyPIStatsTarget,
    PipTrendsTarget,
    ClickPyTarget,
    SafetyDBTarget,
    # Multi-ecosystem
    SnykTarget,
    LibrariesIOTarget,
    DepsDevTarget,
    EcosystemsTarget,
    # npm
    NPMTarget,
    BundlephobiaTarget,
    PackagephobiaTarget,
    NPMStatTarget,
    # Rust
    CratesTarget,
    LibRsTarget,
    # Other ecosystems
    GemsTarget,
    PackagistTarget,
    PubTarget,
    HexTarget,
    NuGetTarget,
    MultiEcosystemTarget,
    Target,
)

# Explicit registry of all available targets
REGISTRY: dict[str, type[Target]] = {
    # Git targets
    "origin": OriginTarget,
    "upstream": UpstreamTarget,
    "issues": IssuesTarget,
    "pulls": PullsTarget,
    "actions": ActionsTarget,
    "wiki": WikiTarget,
    "releases": ReleasesTarget,
    "branches": BranchesTarget,
    "commits": CommitsTarget,
    "security": SecurityTarget,
    "discussions": DiscussionsTarget,
    # Python / PyPI targets
    "pypi": PyPITarget,
    "inspector": InspectorTarget,
    "pypi-json": PyPIJSONTarget,
    "pepy": PePyTarget,
    "pypistats": PyPIStatsTarget,
    "piptrends": PipTrendsTarget,
    "clickpy": ClickPyTarget,
    "snyk": SnykTarget,
    "safety-db": SafetyDBTarget,
    # Multi-ecosystem targets
    "libraries-io": LibrariesIOTarget,
    "deps": DepsDevTarget,
    "ecosystems": EcosystemsTarget,
    # npm targets
    "npm": NPMTarget,
    "bundlephobia": BundlephobiaTarget,
    "packagephobia": PackagephobiaTarget,
    "npm-stat": NPMStatTarget,
    # Rust targets
    "crates": CratesTarget,
    "librs": LibRsTarget,
    # Other ecosystem targets
    "gems": GemsTarget,
    "packagist": PackagistTarget,
    "pub": PubTarget,
    "hex": HexTarget,
    "nuget": NuGetTarget,
    # Service targets
    "codecov": CodecovTarget,
    "coveralls": CoverallsTarget,
}


def get_target(name: str) -> Target:
    """Get a target instance by name.

    Supports suffix notation for multi-ecosystem targets:
    - "snyk" - auto-detect ecosystem
    - "snyk:pypi" - explicit Python ecosystem
    - "deps:npm" - explicit npm ecosystem
    """
    if ":" in name:
        base_name, ecosystem = name.split(":", 1)
    else:
        base_name, ecosystem = name, None

    if base_name not in REGISTRY:
        available = ", ".join(sorted(REGISTRY.keys()))
        raise UnknownTargetError(
            f"Unknown target: '{base_name}'. Available targets: {available}"
        )

    target_cls = REGISTRY[base_name]

    if ecosystem is not None:
        if not issubclass(target_cls, MultiEcosystemTarget):
            raise UnknownTargetError(
                f"Target '{base_name}' doesn't support ecosystem suffix. "
                f"Use '{base_name}' without suffix."
            )
        supported = sorted(target_cls.ecosystem_url_map.keys())
        if ecosystem not in target_cls.ecosystem_url_map:
            raise UnknownTargetError(
                f"Target '{base_name}' doesn't support ecosystem '{ecosystem}'. "
                f"Supported: {', '.join(supported)}"
            )
        return target_cls(ecosystem=ecosystem)

    return target_cls()


def list_targets() -> list[tuple[str, str]]:
    """List all available targets with their descriptions."""
    return [(name, entry.description) for name, entry in sorted(REGISTRY.items())]
