"""Project metadata: git remotes, ecosystem detection, package name extraction.

Git note: This module reads .git/config directly instead of calling git commands.
This is faster but has limitations:
- Does not support [url "..."].insteadOf rewrites
- Does not support [include] directives in git config
- Does not support GitLab subgroups (e.g., group/subgroup/repo).
  URLs like git@gitlab.com:group/subgroup/repo.git will match but produce
  owner="group" and repo="subgroup/repo", generating incorrect URLs.
- Platform detection uses a hostname heuristic fallback (e.g., "gitlab" in host).
  Self-hosted Gitea, Forgejo, or other GitHub-compatible forges will raise
  UnknownPlatformError unless their hostname contains "github", "gitlab",
  or "bitbucket".
"""

import configparser
import json
import logging
import re
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from olink.core.exceptions import (
    NotGitRepoError,
    ProjectMetadataError,
    UnknownPlatformError,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Git remote parsing
# =============================================================================

SSH_PATTERN = re.compile(
    r"^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$"
)
HTTPS_PATTERN = re.compile(
    r"^https?://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$"
)
GIT_PATTERN = re.compile(
    r"^git://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$"
)

HOST_TO_PLATFORM = {
    "github.com": "github",
    "www.github.com": "github",
    "gitlab.com": "gitlab",
    "www.gitlab.com": "gitlab",
    "bitbucket.org": "bitbucket",
    "www.bitbucket.org": "bitbucket",
}


@dataclass
class ParsedRemote:
    """Parsed git remote URL."""

    platform: str
    host: str
    owner: str
    repo: str

    @property
    def base_url(self) -> str:
        """Get the base URL for this remote."""
        return f"https://{self.host}/{self.owner}/{self.repo}"


def _get_git_dir(cwd: str) -> Path | None:
    """Get the .git directory path, handling worktrees and submodules."""
    git_path = Path(cwd) / ".git"

    if not git_path.exists():
        return None

    if git_path.is_dir():
        return git_path

    if git_path.is_file():
        content = git_path.read_text().strip()
        if content.startswith("gitdir:"):
            gitdir_str = content[7:].strip()
            gitdir_path = Path(gitdir_str)
            if not gitdir_path.is_absolute():
                gitdir_path = (Path(cwd) / gitdir_path).resolve()
            return gitdir_path

    return None


def _read_git_config(cwd: str) -> configparser.ConfigParser:
    """Read and parse .git/config file."""
    git_dir = _get_git_dir(cwd)
    if git_dir is None:
        raise NotGitRepoError(f"'{cwd}' is not inside a git repository")

    config_path = git_dir / "config"
    if not config_path.exists():
        raise NotGitRepoError(f"'{cwd}' is not inside a git repository")

    config = configparser.ConfigParser()
    with open(config_path, encoding="utf-8") as f:
        config.read_file(f)
    return config


def get_remote_url(cwd: str, remote_name: str = "origin") -> str | None:
    """Get the URL for a git remote.

    Note: Does not apply [url].insteadOf rewrites.
    """
    config = _read_git_config(cwd)

    section = f'remote "{remote_name}"'
    if section not in config:
        return None

    return config.get(section, "url", fallback=None)


def parse_remote_url(url: str) -> ParsedRemote:
    """Parse a git remote URL into its components."""
    for pattern in [SSH_PATTERN, HTTPS_PATTERN, GIT_PATTERN]:
        match = pattern.match(url)
        if match:
            host = match.group("host")
            owner = match.group("owner")
            repo = match.group("repo")

            platform = HOST_TO_PLATFORM.get(host.lower())
            if platform is None:
                if "gitlab" in host.lower():
                    platform = "gitlab"
                elif "github" in host.lower():
                    platform = "github"
                elif "bitbucket" in host.lower():
                    platform = "bitbucket"
                else:
                    raise UnknownPlatformError(f"Unknown git hosting platform: {host}")

            if "/" in repo:
                logger.warning(
                    "Repo path '%s/%s' contains subgroups — generated URLs may be incorrect. "
                    "See module docstring for details.",
                    owner,
                    repo,
                )

            return ParsedRemote(
                platform=platform,
                host=host,
                owner=owner,
                repo=repo,
            )

    raise UnknownPlatformError(f"Could not parse remote URL: {url}")


# =============================================================================
# Ecosystem detection & package name extraction
# =============================================================================


class EcosystemConfig:
    """Configuration for an ecosystem."""

    def __init__(
        self,
        name: str,
        display_name: str,
        config_file: str,
        get_package_name: Callable[[str], str],
    ):
        self.name = name
        self.display_name = display_name
        self.config_file = config_file
        self.get_package_name = get_package_name

    def exists(self, cwd: str) -> bool:
        """Check if this ecosystem's config file exists."""
        if "*" in self.config_file:
            return bool(list(Path(cwd).glob(self.config_file)))
        return (Path(cwd) / self.config_file).exists()


def _get_pypi_name(cwd: str) -> str:
    """Extract package name from pyproject.toml."""
    pyproject_path = Path(cwd) / "pyproject.toml"
    if not pyproject_path.exists():
        raise ProjectMetadataError("No pyproject.toml found")

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ProjectMetadataError(f"Invalid pyproject.toml: {e}") from e

    name = data.get("project", {}).get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'project.name' in pyproject.toml")
    return name


def _get_npm_name(cwd: str) -> str:
    """Extract package name from package.json."""
    package_json_path = Path(cwd) / "package.json"
    if not package_json_path.exists():
        raise ProjectMetadataError("No package.json found")

    try:
        with open(package_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ProjectMetadataError(f"Invalid package.json: {e}") from e

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'name' in package.json")
    return name


def _get_cargo_name(cwd: str) -> str:
    """Extract package name from Cargo.toml."""
    cargo_path = Path(cwd) / "Cargo.toml"
    if not cargo_path.exists():
        raise ProjectMetadataError("No Cargo.toml found")

    try:
        with open(cargo_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ProjectMetadataError(f"Invalid Cargo.toml: {e}") from e

    name = data.get("package", {}).get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'package.name' in Cargo.toml")
    return name


def _get_go_name(cwd: str) -> str:
    """Extract module name from go.mod."""
    go_mod_path = Path(cwd) / "go.mod"
    if not go_mod_path.exists():
        raise ProjectMetadataError("No go.mod found")

    content = go_mod_path.read_text(encoding="utf-8")
    match = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
    if not match:
        raise ProjectMetadataError("No 'module' declaration in go.mod")
    return match.group(1)


def _get_gems_name(cwd: str) -> str:
    """Extract gem name from *.gemspec."""
    gemspec_files = list(Path(cwd).glob("*.gemspec"))
    if not gemspec_files:
        raise ProjectMetadataError("No .gemspec file found")
    content = gemspec_files[0].read_text(encoding="utf-8")
    match = re.search(r"""\w+\.name\s*=\s*['"]([^'"]+)['"]""", content)
    if not match:
        raise ProjectMetadataError("No 'name' in .gemspec file")
    return match.group(1)


def _get_packagist_name(cwd: str) -> str:
    """Extract package name from composer.json."""
    composer_path = Path(cwd) / "composer.json"
    if not composer_path.exists():
        raise ProjectMetadataError("No composer.json found")

    try:
        with open(composer_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ProjectMetadataError(f"Invalid composer.json: {e}") from e

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'name' in composer.json")
    return name


def _get_pub_name(cwd: str) -> str:
    """Extract package name from pubspec.yaml."""
    pubspec_path = Path(cwd) / "pubspec.yaml"
    if not pubspec_path.exists():
        raise ProjectMetadataError("No pubspec.yaml found")

    content = pubspec_path.read_text(encoding="utf-8")
    match = re.search(r"^name:\s*['\"]?([^\s'\"]+)['\"]?", content, re.MULTILINE)
    if not match:
        raise ProjectMetadataError("No 'name' in pubspec.yaml")
    return match.group(1)


def _get_hex_name(cwd: str) -> str:
    """Extract app name from mix.exs."""
    mix_path = Path(cwd) / "mix.exs"
    if not mix_path.exists():
        raise ProjectMetadataError("No mix.exs found")
    content = mix_path.read_text(encoding="utf-8")
    match = re.search(r"""app:\s*:(\w+)""", content)
    if not match:
        raise ProjectMetadataError("No 'app' in mix.exs")
    return match.group(1)


def _get_nuget_name(cwd: str) -> str:
    """Extract package name from *.csproj."""
    csproj_files = list(Path(cwd).glob("*.csproj"))
    if not csproj_files:
        raise ProjectMetadataError("No .csproj file found")
    content = csproj_files[0].read_text(encoding="utf-8")
    match = re.search(r"<PackageId>([^<]+)</PackageId>", content)
    if not match:
        return csproj_files[0].stem
    return match.group(1)


def _get_open_vsx_name(cwd: str) -> str:
    """Align extension target URLs with extension metadata already kept in package.json."""
    package_json_path = Path(cwd) / "package.json"
    if not package_json_path.exists():
        raise ProjectMetadataError("No package.json found")

    try:
        with open(package_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ProjectMetadataError(f"Invalid package.json: {e}") from e

    publisher = data.get("publisher")
    name = data.get("name")
    if not publisher or not isinstance(publisher, str):
        raise ProjectMetadataError("No 'publisher' in package.json for open-vsx")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'name' in package.json")

    return f"{publisher}.{name}"


def _get_maven_name(cwd: str) -> str:
    """Use Maven coordinates so artifact links stay stable across tooling and mirrors."""
    pom_path = Path(cwd) / "pom.xml"
    if not pom_path.exists():
        raise ProjectMetadataError("No pom.xml found")

    try:
        root = ET.fromstring(pom_path.read_text(encoding="utf-8"))
    except ET.ParseError as e:
        raise ProjectMetadataError(f"Invalid pom.xml: {e}") from e

    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}", 1)[0] + "}"

    group_id = root.findtext(f"{namespace}groupId")
    if not group_id:
        parent = root.find(f"{namespace}parent")
        if parent is not None:
            group_id = parent.findtext(f"{namespace}groupId")

    artifact_id = root.findtext(f"{namespace}artifactId")
    if not group_id or not artifact_id:
        raise ProjectMetadataError("No 'groupId'/'artifactId' in pom.xml")

    return f"{group_id}:{artifact_id}"


def _get_hackage_name(cwd: str) -> str:
    """Read Cabal metadata directly to avoid external tool dependencies during lookup."""
    cabal_files = list(Path(cwd).glob("*.cabal"))
    if not cabal_files:
        raise ProjectMetadataError("No .cabal file found")

    content = cabal_files[0].read_text(encoding="utf-8")
    match = re.search(r"^name\s*:\s*(\S+)", content, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ProjectMetadataError("No 'name' in .cabal file")
    return match.group(1)


def _get_cpan_name(cwd: str) -> str:
    """Prefer cpanfile metadata because it is common in modern Perl distribution layouts."""
    cpanfile_path = Path(cwd) / "cpanfile"
    if not cpanfile_path.exists():
        raise ProjectMetadataError("No cpanfile found")

    content = cpanfile_path.read_text(encoding="utf-8")
    match = re.search(r"requires\s+['\"]([^'\"]+)['\"]", content)
    if not match:
        raise ProjectMetadataError("No module name in cpanfile")
    return match.group(1)


ECOSYSTEMS: dict[str, EcosystemConfig] = {
    "pypi": EcosystemConfig("pypi", "Python", "pyproject.toml", _get_pypi_name),
    "npm": EcosystemConfig("npm", "npm", "package.json", _get_npm_name),
    "cargo": EcosystemConfig("cargo", "Rust", "Cargo.toml", _get_cargo_name),
    "go": EcosystemConfig("go", "Go", "go.mod", _get_go_name),
    "gems": EcosystemConfig("gems", "Ruby", "*.gemspec", _get_gems_name),
    "packagist": EcosystemConfig(
        "packagist", "PHP", "composer.json", _get_packagist_name
    ),
    "pub": EcosystemConfig("pub", "Dart", "pubspec.yaml", _get_pub_name),
    "hex": EcosystemConfig("hex", "Elixir", "mix.exs", _get_hex_name),
    "nuget": EcosystemConfig("nuget", ".NET", "*.csproj", _get_nuget_name),
    "open-vsx": EcosystemConfig(
        "open-vsx", "Open VSX", "package.json", _get_open_vsx_name
    ),
    "maven": EcosystemConfig("maven", "Maven", "pom.xml", _get_maven_name),
    "hackage": EcosystemConfig("hackage", "Haskell", "*.cabal", _get_hackage_name),
    "cpan": EcosystemConfig("cpan", "Perl", "cpanfile", _get_cpan_name),
}


def detect_ecosystems(cwd: str) -> list[str]:
    """Detect which ecosystems are present in the given directory."""
    detected: list[str] = []
    for name, config in ECOSYSTEMS.items():
        if config.exists(cwd):
            try:
                config.get_package_name(cwd)
                detected.append(name)
            except ProjectMetadataError as e:
                logger.warning("%s found but skipped: %s", config.config_file, e)
    return detected


def get_package_name(cwd: str, ecosystem: str) -> str:
    """Get the package name for a specific ecosystem."""
    if ecosystem not in ECOSYSTEMS:
        available = ", ".join(sorted(ECOSYSTEMS.keys()))
        raise ProjectMetadataError(
            f"Unknown ecosystem: '{ecosystem}'. Available: {available}"
        )
    return ECOSYSTEMS[ecosystem].get_package_name(cwd)
