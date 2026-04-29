"""Project metadata: git remotes, ecosystem detection, package name extraction.

Git note: This module reads .git/config directly instead of calling git commands.
This is faster but has limitations:
- Supports [url "..."].insteadOf rewrites (longest-match prefix wins).
- Does not support [include] directives in git config (no recursive merging).
- Recognized platforms: github, gitlab, bitbucket, gitea, forgejo (incl. codeberg).
  Hostname heuristic falls back when host is not the canonical SaaS one
  (self-hosted GitHub Enterprise, GitLab CE, Gitea, Forgejo).
- GitLab subgroups (e.g., group/subgroup/repo) are parsed as owner="group"
  and repo="subgroup/repo". The generated URL https://host/group/subgroup/repo
  is correct for GitLab, but may not work for other platforms with nested paths.
"""

import configparser
import json
import logging
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import defusedxml
import defusedxml.ElementTree as ET

from olink.core.exceptions import (
    NotGitRepoError,
    ProjectMetadataError,
    UnknownPlatformError,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Git remote parsing
# =============================================================================

SSH_PATTERN = re.compile(r"^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$")
HTTPS_PATTERN = re.compile(r"^https?://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$")
GIT_PATTERN = re.compile(r"^git://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$")

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


def _parse_git_config(text: str) -> configparser.ConfigParser:
    """Parse already-loaded .git/config text (parsed view; loses duplicate options)."""
    config = configparser.ConfigParser(strict=False)
    config.read_string(text)
    return config


_URL_SECTION_RE = re.compile(r'^\s*\[url\s+"(?P<url>[^"]+)"\]\s*$')
_SECTION_HEADER_RE = re.compile(r"^\s*\[")
_INSTEADOF_RE = re.compile(r"^\s*insteadof\s*=\s*(?P<value>.*)$", re.IGNORECASE)
_TRAILING_COMMENT_RE = re.compile(r"\s+[#;].*$")


def _strip_git_config_value(raw: str) -> str:
    """Strip surrounding whitespace and trailing ` # ...` / ` ; ...` comments.

    Git treats `#` and `;` as comment markers when preceded by whitespace; values
    must drop them so `insteadOf = github: # alias` doesn't capture the comment.
    """
    no_comment = _TRAILING_COMMENT_RE.sub("", raw)
    return no_comment.strip()


def _collect_insteadof_rewrites(config_text: str) -> list[tuple[str, str]]:
    """Scan raw git config text for [url "<rewritten>"].insteadOf entries.

    Why a raw scanner: configparser collapses duplicate options to a single
    value (last-wins with strict=False), but git supports *multiple* `insteadOf`
    lines per `[url "..."]` section — each adds another rewrite rule. The raw
    scanner preserves all entries.

    Sorted longest-prefix-first to match git's longest-match resolution.
    """
    rules: list[tuple[str, str]] = []
    current_url: str | None = None
    for line in config_text.splitlines():
        url_match = _URL_SECTION_RE.match(line)
        if url_match:
            current_url = url_match.group("url")
            continue
        if _SECTION_HEADER_RE.match(line):
            current_url = None
            continue
        if current_url is None:
            continue
        io_match = _INSTEADOF_RE.match(line)
        if io_match:
            value = _strip_git_config_value(io_match.group("value"))
            if value:
                rules.append((value, current_url))
    rules.sort(key=lambda r: len(r[0]), reverse=True)
    return rules


def _apply_insteadof(url: str, rules: list[tuple[str, str]]) -> str:
    """Apply first matching insteadOf rewrite (rules already sorted longest-first)."""
    for prefix, rewritten in rules:
        if url.startswith(prefix):
            return rewritten + url[len(prefix) :]
    return url


def _read_git_config_text(cwd: str) -> str:
    """Read raw .git/config text, mapping permission/encoding errors to NotGitRepoError."""
    git_dir = _get_git_dir(cwd)
    if git_dir is None:
        raise NotGitRepoError(f"'{cwd}' is not inside a git repository")
    config_path = git_dir / "config"
    if not config_path.exists():
        raise NotGitRepoError(f"'{cwd}' is not inside a git repository")
    try:
        return config_path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise NotGitRepoError(f"Cannot read git config: {e}") from e
    except UnicodeDecodeError as e:
        raise NotGitRepoError(f"Git config has invalid UTF-8: {e}") from e


def get_remote_url(cwd: str, remote_name: str = "origin") -> str | None:
    """Get the URL for a git remote, applying [url].insteadOf rewrites if configured."""
    config_text = _read_git_config_text(cwd)
    config = _parse_git_config(config_text)

    section = f'remote "{remote_name}"'
    if section not in config:
        return None

    raw_url = config.get(section, "url", fallback=None)
    if raw_url is None:
        return None
    rules = _collect_insteadof_rewrites(config_text)
    return _apply_insteadof(raw_url, rules)


_SELF_HOSTED_LABEL_TO_PLATFORM = {
    "gitea": "gitea",
    "forgejo": "forgejo",
    "codeberg": "forgejo",
}

_HOST_LABEL_TO_PLATFORM: dict[str, str] = {
    host.split(".", 1)[0]: platform
    for host, platform in HOST_TO_PLATFORM.items()
    if not host.startswith("www.")
} | _SELF_HOSTED_LABEL_TO_PLATFORM

_LABEL_BOUNDARY_RE = re.compile(r"[0-9-]")


def _detect_platform_from_labels(host: str) -> str | None:
    """Detect platform from hostname labels (DNS components), not arbitrary substrings.

    A label matches a platform keyword if it equals the keyword or starts with
    `<keyword>` followed by a digit or `-`. So `gitlab01`, `github-enterprise`,
    `gitea2` match; `gitlabby` does not.
    """
    for label in host.lower().split("."):
        if (platform := _HOST_LABEL_TO_PLATFORM.get(label)) is not None:
            return platform
        for keyword, platform in _HOST_LABEL_TO_PLATFORM.items():
            if (
                label.startswith(keyword)
                and len(label) > len(keyword)
                and _LABEL_BOUNDARY_RE.match(label[len(keyword)])
            ):
                return platform
    return None


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
                platform = _detect_platform_from_labels(host)
            if platform is None:
                raise UnknownPlatformError(f"Unknown git hosting platform: {host}")

            if "/" in repo:
                logger.debug(
                    "Repo path '%s/%s' contains nested groups (e.g. GitLab subgroups).",
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
    """Configuration for an ecosystem.

    `config_file` is the canonical filename (or glob) used by the simple existence
    check. `extra_signals` lists additional filename globs that also count as
    "ecosystem present" — used for ecosystems where multiple, equally-valid
    metadata layouts exist (e.g. CPAN's Makefile.PL / dist.ini / lib/*.pm).
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        config_file: str,
        get_package_name: Callable[[str], str],
        extra_signals: tuple[str, ...] = (),
    ):
        self.name = name
        self.display_name = display_name
        self.config_file = config_file
        self.get_package_name = get_package_name
        self.extra_signals = extra_signals

    def exists(self, cwd: str) -> bool:
        """Check if this ecosystem's config file (or any extra signal) exists.

        Glob results are sorted so detection is deterministic across filesystems.
        """
        candidates = (self.config_file, *self.extra_signals)
        for pattern in candidates:
            if "*" in pattern:
                if sorted(Path(cwd).glob(pattern)):
                    return True
            elif (Path(cwd) / pattern).exists():
                return True
        return False


def _read_text(path: Path, label: str) -> str:
    """Read a text config file, mapping OS/encoding errors to ProjectMetadataError.

    Centralizes the "missing perms / non-UTF8" handling all extractors need so
    CLI consistently surfaces OlinkError messages instead of bare tracebacks.
    """
    try:
        return path.read_text(encoding="utf-8")
    except PermissionError as e:
        raise ProjectMetadataError(f"Cannot read {label}: {e}") from e
    except UnicodeDecodeError as e:
        raise ProjectMetadataError(f"Invalid {label} (non-UTF-8): {e}") from e


def _get_pypi_name(cwd: str) -> str:
    """Read PEP 621 [project].name from pyproject.toml.

    Raises ProjectMetadataError if file missing, TOML invalid, or name absent.
    Does not resolve dynamic = ["name"] — only static metadata supported.
    """
    pyproject_path = Path(cwd) / "pyproject.toml"
    if not pyproject_path.exists():
        raise ProjectMetadataError("No pyproject.toml found")

    content = _read_text(pyproject_path, "pyproject.toml")
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as e:
        raise ProjectMetadataError(f"Invalid pyproject.toml: {e}") from e

    name = data.get("project", {}).get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'project.name' in pyproject.toml")
    return str(name)


def _get_npm_name(cwd: str) -> str:
    """Read top-level "name" from package.json.

    Returns scoped names (@org/pkg) verbatim — callers handle URL encoding.
    Raises ProjectMetadataError if file missing, JSON invalid, or name absent.
    """
    package_json_path = Path(cwd) / "package.json"
    if not package_json_path.exists():
        raise ProjectMetadataError("No package.json found")

    content = _read_text(package_json_path, "package.json")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ProjectMetadataError(f"Invalid package.json: {e}") from e

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'name' in package.json")
    return str(name)


def _get_cargo_name(cwd: str) -> str:
    """Read [package].name from Cargo.toml.

    Workspace-only manifests (no [package] table) raise ProjectMetadataError.
    """
    cargo_path = Path(cwd) / "Cargo.toml"
    if not cargo_path.exists():
        raise ProjectMetadataError("No Cargo.toml found")

    content = _read_text(cargo_path, "Cargo.toml")
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as e:
        raise ProjectMetadataError(f"Invalid Cargo.toml: {e}") from e

    name = data.get("package", {}).get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'package.name' in Cargo.toml")
    return str(name)


def _get_go_name(cwd: str) -> str:
    """Read first `module <path>` declaration from go.mod.

    Returns full module path (e.g. github.com/user/repo). Raises if file
    missing or no module directive present.
    """
    go_mod_path = Path(cwd) / "go.mod"
    if not go_mod_path.exists():
        raise ProjectMetadataError("No go.mod found")

    content = _read_text(go_mod_path, "go.mod")
    match = re.search(r"^module\s+(\S+)", content, re.MULTILINE)
    if not match:
        raise ProjectMetadataError("No 'module' declaration in go.mod")
    return match.group(1)


def _get_gems_name(cwd: str) -> str:
    """Read spec.name = '...' from first matching *.gemspec.

    Picks first glob match if multiple gemspecs exist (rare). Regex assumes
    standard `<var>.name = "..."` form — won't catch dynamically computed names.
    """
    gemspec_files = sorted(Path(cwd).glob("*.gemspec"))
    if not gemspec_files:
        raise ProjectMetadataError("No .gemspec file found")
    content = _read_text(gemspec_files[0], gemspec_files[0].name)
    match = re.search(r"""\w+\.name\s*=\s*['"]([^'"]+)['"]""", content)
    if not match:
        raise ProjectMetadataError("No 'name' in .gemspec file")
    return match.group(1)


def _get_packagist_name(cwd: str) -> str:
    """Read top-level "name" from composer.json (vendor/package format).

    Packagist requires vendor/package — value returned verbatim, no validation.
    """
    composer_path = Path(cwd) / "composer.json"
    if not composer_path.exists():
        raise ProjectMetadataError("No composer.json found")

    content = _read_text(composer_path, "composer.json")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ProjectMetadataError(f"Invalid composer.json: {e}") from e

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'name' in composer.json")
    return str(name)


def _get_pub_name(cwd: str) -> str:
    """Read `name:` key from pubspec.yaml (line-level regex, no YAML parser).

    Avoids pulling a YAML dependency for one field. Won't handle multi-line
    or quoted-key forms — only the canonical `name: value` style pub uses.
    """
    pubspec_path = Path(cwd) / "pubspec.yaml"
    if not pubspec_path.exists():
        raise ProjectMetadataError("No pubspec.yaml found")

    content = _read_text(pubspec_path, "pubspec.yaml")
    match = re.search(r"^name:\s*['\"]?([^\s'\"]+)['\"]?", content, re.MULTILINE)
    if not match:
        raise ProjectMetadataError("No 'name' in pubspec.yaml")
    return match.group(1)


def _get_hex_name(cwd: str) -> str:
    """Extract `app: :name` atom from mix.exs (Elixir build script).

    Hex.pm uses the OTP app atom as the package slug. Regex won't match
    dynamic computed atoms — those are uncommon in published packages.
    """
    mix_path = Path(cwd) / "mix.exs"
    if not mix_path.exists():
        raise ProjectMetadataError("No mix.exs found")
    content = _read_text(mix_path, "mix.exs")
    match = re.search(r"""app:\s*:(\w+)""", content)
    if not match:
        raise ProjectMetadataError("No 'app' in mix.exs")
    return match.group(1)


def _get_nuget_name(cwd: str) -> str:
    """Read <PackageId> from first *.csproj, fall back to filename stem.

    .NET convention: when <PackageId> is absent, NuGet uses the project file
    name as the package id. Mirrors that behavior.
    """
    csproj_files = sorted(Path(cwd).glob("*.csproj"))
    if not csproj_files:
        raise ProjectMetadataError("No .csproj file found")
    content = _read_text(csproj_files[0], csproj_files[0].name)
    match = re.search(r"<PackageId>([^<]+)</PackageId>", content)
    if not match:
        return csproj_files[0].stem
    return match.group(1)


def get_open_vsx_name(cwd: str) -> str:
    """Build `publisher.name` extension id from package.json.

    Open VSX (and VS Code Marketplace) identify extensions by publisher + name.
    Both fields required — raises ProjectMetadataError if either missing.
    Caller must split on '.' to extract URL components.
    """
    package_json_path = Path(cwd) / "package.json"
    if not package_json_path.exists():
        raise ProjectMetadataError("No package.json found")

    content = _read_text(package_json_path, "package.json")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ProjectMetadataError(f"Invalid package.json: {e}") from e

    publisher = data.get("publisher")
    name = data.get("name")
    if not publisher or not isinstance(publisher, str):
        raise ProjectMetadataError("No 'publisher' in package.json for open-vsx")
    if not name or not isinstance(name, str):
        raise ProjectMetadataError("No 'name' in package.json")

    return f"{publisher}.{name}"


_MAVEN_PARENT_DEPTH = 8


def _parse_pom(pom_path: Path) -> tuple[ET.Element, str]:
    """Parse a pom.xml and return (root, namespace_prefix). Raises ProjectMetadataError."""
    content = _read_text(pom_path, "pom.xml")
    try:
        root = ET.fromstring(content)
    except defusedxml.DefusedXmlException as e:
        raise ProjectMetadataError(f"pom.xml contains disallowed XML features: {e}") from e
    except ET.ParseError as e:
        raise ProjectMetadataError(f"Invalid pom.xml: {e}") from e
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}", 1)[0] + "}"
    return root, namespace


def _get_maven_name(cwd: str) -> str:
    """Resolve Maven groupId:artifactId, walking <parent> chain via <relativePath> when needed.

    Why recursive: Maven inheritance can span multiple levels (corporate parent ->
    product parent -> service artifact). One-level lookup misses grandparent groupId.
    Walks at most _MAVEN_PARENT_DEPTH ancestors to bound work and prevent cycles.
    """
    pom_path = Path(cwd) / "pom.xml"
    if not pom_path.exists():
        raise ProjectMetadataError("No pom.xml found")

    root, ns = _parse_pom(pom_path)

    artifact_id = root.findtext(f"{ns}artifactId")
    if not artifact_id:
        raise ProjectMetadataError("No 'artifactId' in pom.xml")

    group_id = root.findtext(f"{ns}groupId")
    current_pom = pom_path
    current_root = root
    current_ns = ns
    depth = 0
    while not group_id and depth < _MAVEN_PARENT_DEPTH:
        parent = current_root.find(f"{current_ns}parent")
        if parent is None:
            break
        group_id = parent.findtext(f"{current_ns}groupId")
        if group_id:
            break
        relative = (parent.findtext(f"{current_ns}relativePath") or "../pom.xml").strip()
        if not relative:
            break
        next_pom = (current_pom.parent / relative).resolve()
        if next_pom.is_dir():
            next_pom = next_pom / "pom.xml"
        if not next_pom.exists() or next_pom == current_pom:
            break
        current_pom = next_pom
        current_root, current_ns = _parse_pom(next_pom)
        group_id = current_root.findtext(f"{current_ns}groupId")
        depth += 1

    if not group_id:
        raise ProjectMetadataError("No 'groupId' in pom.xml or parent chain")

    return f"{group_id}:{artifact_id}"


def _get_hackage_name(cwd: str) -> str:
    """Read `name:` field from first *.cabal file (case-insensitive).

    Direct read avoids cabal/ghc dependency. Cabal field names are case-insensitive
    per spec — regex uses re.IGNORECASE.
    """
    cabal_files = sorted(Path(cwd).glob("*.cabal"))
    if not cabal_files:
        raise ProjectMetadataError("No .cabal file found")

    content = _read_text(cabal_files[0], cabal_files[0].name)
    match = re.search(r"^name\s*:\s*(\S+)", content, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ProjectMetadataError("No 'name' in .cabal file")
    return match.group(1)


def _get_cpan_name(cwd: str) -> str:
    """Infer the primary CPAN module name from distribution metadata.

    Checks Makefile.PL first (authoritative), then lib/ directory layout
    (reliable), then dist.ini as a last resort — the dist.ini hyphen-to-colon
    conversion is a heuristic that can be wrong for distributions whose name
    doesn't mirror the main module.
    """
    root = Path(cwd)

    # 1. Makefile.PL: NAME => 'My::Dist' (most reliable — author-specified)
    makefile_pl = root / "Makefile.PL"
    if makefile_pl.exists():
        content = _read_text(makefile_pl, "Makefile.PL")
        match = re.search(r"NAME\s*=>\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)
        logger.debug("Makefile.PL found but NAME not parseable, trying lib/ layout")

    # 2. Directory layout: lib/Foo/Bar.pm -> Foo::Bar (prefer shallowest module)
    lib_dir = root / "lib"
    if lib_dir.exists() and lib_dir.is_dir():
        pm_files = sorted(
            lib_dir.rglob("*.pm"),
            key=lambda p: (len(p.parts), p.as_posix()),
        )
        for pm in pm_files:
            try:
                rel = pm.relative_to(lib_dir)
            except ValueError:
                continue
            module = rel.with_suffix("").as_posix().replace("/", "::")
            if module:
                logger.debug("CPAN module name inferred from lib/ layout as '%s'", module)
                return module

    # 3. dist.ini (Dist::Zilla): name = My-Dist (heuristic — hyphen-to-colon)
    dist_ini_path = root / "dist.ini"
    if dist_ini_path.exists():
        content = _read_text(dist_ini_path, "dist.ini")
        match = re.search(r"^name\s*=\s*(\S+)", content, re.MULTILINE)
        if match:
            return match.group(1).strip().replace("-", "::")
        logger.debug("dist.ini found but name not parseable")

    raise ProjectMetadataError("Could not determine CPAN module name from project metadata")


ECOSYSTEMS: dict[str, EcosystemConfig] = {
    "pypi": EcosystemConfig("pypi", "Python", "pyproject.toml", _get_pypi_name),
    "npm": EcosystemConfig("npm", "npm", "package.json", _get_npm_name),
    "cargo": EcosystemConfig("cargo", "Rust", "Cargo.toml", _get_cargo_name),
    "go": EcosystemConfig("go", "Go", "go.mod", _get_go_name),
    "gems": EcosystemConfig("gems", "Ruby", "*.gemspec", _get_gems_name),
    "packagist": EcosystemConfig("packagist", "PHP", "composer.json", _get_packagist_name),
    "pub": EcosystemConfig("pub", "Dart", "pubspec.yaml", _get_pub_name),
    "hex": EcosystemConfig("hex", "Elixir", "mix.exs", _get_hex_name),
    "nuget": EcosystemConfig("nuget", ".NET", "*.csproj", _get_nuget_name),
    "maven": EcosystemConfig("maven", "Maven", "pom.xml", _get_maven_name),
    "hackage": EcosystemConfig("hackage", "Haskell", "*.cabal", _get_hackage_name),
    "cpan": EcosystemConfig(
        "cpan",
        "Perl",
        "Makefile.PL",
        _get_cpan_name,
        extra_signals=("dist.ini", "lib/*.pm", "lib/**/*.pm"),
    ),
    "open-vsx": EcosystemConfig("open-vsx", "VS Code Extension", "package.json", get_open_vsx_name),
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
        raise ProjectMetadataError(f"Unknown ecosystem: '{ecosystem}'. Available: {available}")
    return ECOSYSTEMS[ecosystem].get_package_name(cwd)
