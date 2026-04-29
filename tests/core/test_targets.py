"""Tests for targets.py - Target URL generation."""

import subprocess
from pathlib import Path

import pytest

from olink.core.exceptions import (
    NoRemoteError,
    ProjectMetadataError,
    UnknownTargetError,
    UnsupportedFeatureError,
)
from olink.core.catalog import REGISTRY, get_target, list_targets
from olink.core.targets import (
    ActionsTarget,
    BranchesTarget,
    BundlephobiaTarget,
    ClickPyTarget,
    CodecovTarget,
    CommitsTarget,
    CoverallsTarget,
    CpanTarget,
    CratesTarget,
    DepsDevTarget,
    DiscussionsTarget,
    DocsRsTarget,
    EcosystemsTarget,
    GemsTarget,
    GoDocsTarget,
    GoPkgTarget,
    HackageTarget,
    HexTarget,
    InspectorTarget,
    IssuesTarget,
    JsDelivrTarget,
    LibRsTarget,
    LibrariesIOTarget,
    MavenTarget,
    MultiEcosystemTarget,
    NPMStatTarget,
    NPMTarget,
    NuGetTarget,
    OpenVSXTarget,
    OriginTarget,
    PackagephobiaTarget,
    PackagistTarget,
    PePyTarget,
    PipTrendsTarget,
    PiWheelsTarget,
    PubTarget,
    PullsTarget,
    PyPIJSONTarget,
    PyPIStatsTarget,
    PyPITarget,
    ReleasesTarget,
    RubyGemsStatsTarget,
    SafetyDBTarget,
    SecurityTarget,
    SkypackTarget,
    SnykTarget,
    SocketTarget,
    UnpkgTarget,
    UpstreamTarget,
    WikiTarget,
)


class TestRegistry:
    """Tests for target registry."""

    def test_all_targets_registered(self) -> None:
        expected_targets = {
            "origin",
            "upstream",
            "issues",
            "pulls",
            "actions",
            "wiki",
            "releases",
            "branches",
            "commits",
            "security",
            "discussions",
            "pypi",
            "inspector",
            "pypi-json",
            "pepy",
            "piwheels",
            "pypistats",
            "piptrends",
            "clickpy",
            "snyk",
            "safety-db",
            "libraries-io",
            "deps",
            "ecosystems",
            "socket",
            "npm",
            "bundlephobia",
            "packagephobia",
            "npm-stat",
            "jsdelivr",
            "unpkg",
            "skypack",
            "crates",
            "librs",
            "docsrs",
            "pkg-go",
            "go-docs",
            "gems",
            "rubygems-stats",
            "packagist",
            "pub",
            "hex",
            "nuget",
            "open-vsx",
            "maven",
            "hackage",
            "cpan",
            "codecov",
            "coveralls",
        }
        assert set(REGISTRY.keys()) == expected_targets

    def test_get_target_returns_instance(self) -> None:
        target = get_target("pypi")
        assert isinstance(target, PyPITarget)

    def test_get_target_unknown_raises(self) -> None:
        with pytest.raises(UnknownTargetError, match="Unknown target"):
            get_target("nonexistent")

    def test_list_targets_returns_all(self) -> None:
        targets = list_targets()
        assert len(targets) == len(REGISTRY)
        names = [name for name, _ in targets]
        assert "origin" in names
        assert "pypi" in names
        assert "pepy" in names
        assert "bundlephobia" in names
        assert "codecov" in names


class TestGitTargets:
    """Tests for git-related targets."""

    def test_origin_target_github(self, temp_git_repo: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo"

    def test_origin_target_https(self, temp_git_repo_https: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_https)
        assert url == "https://github.com/testuser/testrepo"

    def test_origin_target_no_remote(self, temp_dir: str) -> None:
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        target = OriginTarget()
        with pytest.raises(NoRemoteError, match="No 'origin' remote configured"):
            target.get_url(temp_dir)

    def test_upstream_target_no_remote(self, temp_git_repo: str) -> None:
        target = UpstreamTarget()
        with pytest.raises(NoRemoteError, match="No 'upstream' remote configured"):
            target.get_url(temp_git_repo)

    def test_issues_target_github(self, temp_git_repo: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/issues"

    def test_issues_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/issues"

    def test_pulls_target_github(self, temp_git_repo: str) -> None:
        target = PullsTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/pulls"

    def test_pulls_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = PullsTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/merge_requests"

    def test_actions_target_github(self, temp_git_repo: str) -> None:
        target = ActionsTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/actions"

    def test_actions_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = ActionsTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/pipelines"

    def test_wiki_target_github(self, temp_git_repo: str) -> None:
        target = WikiTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/wiki"

    def test_wiki_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = WikiTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/wikis"

    def test_releases_target_github(self, temp_git_repo: str) -> None:
        target = ReleasesTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/releases"

    def test_releases_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = ReleasesTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/releases"

    def test_branches_target_github(self, temp_git_repo: str) -> None:
        target = BranchesTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/branches"

    def test_branches_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = BranchesTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/branches"

    def test_commits_target_github(self, temp_git_repo: str) -> None:
        target = CommitsTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/commits"

    def test_commits_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = CommitsTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/commits"

    def test_security_target_github(self, temp_git_repo: str) -> None:
        target = SecurityTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/security"

    def test_security_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = SecurityTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://gitlab.com/testuser/testrepo/-/security/dashboard"

    def test_discussions_target_github(self, temp_git_repo: str) -> None:
        target = DiscussionsTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://github.com/testuser/testrepo/discussions"

    def test_discussions_target_gitlab_unsupported(self, temp_git_repo_gitlab: str) -> None:
        target = DiscussionsTarget()
        with pytest.raises(UnsupportedFeatureError, match="not available on gitlab"):
            target.get_url(temp_git_repo_gitlab)

    def test_origin_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo"

    def test_origin_target_bitbucket_https(self, temp_git_repo_bitbucket_https: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_bitbucket_https)
        assert url == "https://bitbucket.org/testuser/testrepo"

    def test_issues_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo/issues"

    def test_pulls_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = PullsTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo/pull-requests"

    def test_actions_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = ActionsTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo/pipelines"

    def test_branches_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = BranchesTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo/branches"

    def test_commits_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = CommitsTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo/commits"

    def test_releases_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = ReleasesTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://bitbucket.org/testuser/testrepo/downloads"

    def test_security_target_bitbucket_unsupported(self, temp_git_repo_bitbucket: str) -> None:
        target = SecurityTarget()
        with pytest.raises(UnsupportedFeatureError, match="not available on bitbucket"):
            target.get_url(temp_git_repo_bitbucket)

    def test_discussions_target_bitbucket_unsupported(self, temp_git_repo_bitbucket: str) -> None:
        target = DiscussionsTarget()
        with pytest.raises(UnsupportedFeatureError, match="not available on bitbucket"):
            target.get_url(temp_git_repo_bitbucket)

    def test_upstream_target_with_upstream(self, temp_git_repo_with_upstream: str) -> None:
        target = UpstreamTarget()
        url = target.get_url(temp_git_repo_with_upstream)
        assert url == "https://github.com/original-author/testrepo"

    def test_origin_target_gitea(self, temp_git_repo_gitea: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_gitea)
        assert url == "https://gitea.example.com/testuser/testrepo"

    def test_issues_target_gitea(self, temp_git_repo_gitea: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo_gitea)
        assert url == "https://gitea.example.com/testuser/testrepo/issues"

    def test_pulls_target_gitea(self, temp_git_repo_gitea: str) -> None:
        target = PullsTarget()
        url = target.get_url(temp_git_repo_gitea)
        assert url == "https://gitea.example.com/testuser/testrepo/pulls"

    def test_origin_target_codeberg_forgejo(self, temp_git_repo_codeberg: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_codeberg)
        assert url == "https://codeberg.org/testuser/testrepo"

    def test_issues_target_forgejo(self, temp_git_repo_codeberg: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo_codeberg)
        assert url == "https://codeberg.org/testuser/testrepo/issues"

    def test_origin_target_forgejo_ssh(self, temp_git_repo_forgejo: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_forgejo)
        assert url == "https://forgejo.example.com/testuser/testrepo"

    def test_issues_target_forgejo_ssh(self, temp_git_repo_forgejo: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo_forgejo)
        assert url == "https://forgejo.example.com/testuser/testrepo/issues"

    def test_origin_target_gitea_https(self, temp_git_repo_gitea_https: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_gitea_https)
        assert url == "https://gitea.example.com/testuser/testrepo"

    def test_issues_target_gitea_https(self, temp_git_repo_gitea_https: str) -> None:
        target = IssuesTarget()
        url = target.get_url(temp_git_repo_gitea_https)
        assert url == "https://gitea.example.com/testuser/testrepo/issues"

    def test_origin_target_forgejo_https(self, temp_git_repo_forgejo_https: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_forgejo_https)
        assert url == "https://forgejo.example.com/testuser/testrepo"

    def test_origin_target_codeberg_https(self, temp_git_repo_codeberg_https: str) -> None:
        target = OriginTarget()
        url = target.get_url(temp_git_repo_codeberg_https)
        assert url == "https://codeberg.org/testuser/testrepo"


class TestRegistryTargets:
    """Tests for package registry targets."""

    def test_pypi_target(self, temp_pyproject: str) -> None:
        target = PyPITarget()
        url = target.get_url(temp_pyproject)
        assert url == "https://pypi.org/project/test-project/"

    def test_pypi_target_no_config(self, temp_dir: str) -> None:
        target = PyPITarget()
        with pytest.raises(ProjectMetadataError, match="No pyproject.toml found"):
            target.get_url(temp_dir)

    def test_piwheels_target(self, temp_pyproject: str) -> None:
        """Confirm piwheels URL generation matches the detected Python package name."""
        target = PiWheelsTarget()
        url = target.get_url(temp_pyproject)
        assert url == "https://www.piwheels.org/project/test-project/"

    def test_piwheels_target_no_config(self, temp_dir: str) -> None:
        """Protect user feedback quality when Python metadata cannot be discovered."""
        target = PiWheelsTarget()
        with pytest.raises(ProjectMetadataError, match="No pyproject.toml found"):
            target.get_url(temp_dir)

    def test_npm_target(self, temp_package_json: str) -> None:
        target = NPMTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://www.npmjs.com/package/test-project"

    def test_npm_target_no_config(self, temp_dir: str) -> None:
        target = NPMTarget()
        with pytest.raises(ProjectMetadataError, match="No package.json found"):
            target.get_url(temp_dir)

    def test_npm_target_scoped(self, temp_package_json_scoped: str) -> None:
        target = NPMTarget()
        url = target.get_url(temp_package_json_scoped)
        assert url == "https://www.npmjs.com/package/@myorg/test-project"

    def test_gems_target(self, temp_gemspec: str) -> None:
        target = GemsTarget()
        url = target.get_url(temp_gemspec)
        assert url == "https://rubygems.org/gems/mygem"

    def test_gems_target_no_config(self, temp_dir: str) -> None:
        target = GemsTarget()
        with pytest.raises(ProjectMetadataError, match="No .gemspec file found"):
            target.get_url(temp_dir)

    def test_crates_target(self, temp_cargo_toml: str) -> None:
        target = CratesTarget()
        url = target.get_url(temp_cargo_toml)
        assert url == "https://crates.io/crates/test-crate"

    def test_crates_target_no_config(self, temp_dir: str) -> None:
        target = CratesTarget()
        with pytest.raises(ProjectMetadataError, match="No Cargo.toml found"):
            target.get_url(temp_dir)

    def test_docsrs_target(self, temp_cargo_toml: str) -> None:
        target = DocsRsTarget()
        url = target.get_url(temp_cargo_toml)
        assert url == "https://docs.rs/test-crate"

    def test_docsrs_target_no_config(self, temp_dir: str) -> None:
        target = DocsRsTarget()
        with pytest.raises(ProjectMetadataError, match="No Cargo.toml found"):
            target.get_url(temp_dir)

    def test_pkg_go_target(self, temp_go_mod: str) -> None:
        target = GoPkgTarget()
        url = target.get_url(temp_go_mod)
        assert url == "https://pkg.go.dev/github.com/testuser/test-go-module"

    def test_pkg_go_target_no_config(self, temp_dir: str) -> None:
        target = GoPkgTarget()
        with pytest.raises(ProjectMetadataError, match="No go.mod found"):
            target.get_url(temp_dir)

    def test_go_docs_target(self, temp_go_mod: str) -> None:
        target = GoDocsTarget()
        url = target.get_url(temp_go_mod)
        assert url == "https://pkg.go.dev/github.com/testuser/test-go-module"

    def test_go_docs_target_no_config(self, temp_dir: str) -> None:
        target = GoDocsTarget()
        with pytest.raises(ProjectMetadataError, match="No go.mod found"):
            target.get_url(temp_dir)

    def test_rubygems_stats_target(self, temp_gemspec: str) -> None:
        target = RubyGemsStatsTarget()
        url = target.get_url(temp_gemspec)
        assert url == "https://rubygems.org/gems/mygem/stats"

    def test_rubygems_stats_target_no_config(self, temp_dir: str) -> None:
        target = RubyGemsStatsTarget()
        with pytest.raises(ProjectMetadataError, match="No .gemspec file found"):
            target.get_url(temp_dir)

    def test_jsdelivr_target(self, temp_package_json: str) -> None:
        target = JsDelivrTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://www.jsdelivr.com/package/npm/test-project"

    def test_jsdelivr_target_no_config(self, temp_dir: str) -> None:
        target = JsDelivrTarget()
        with pytest.raises(ProjectMetadataError, match="No package.json found"):
            target.get_url(temp_dir)

    def test_jsdelivr_target_scoped(self, temp_package_json_scoped: str) -> None:
        target = JsDelivrTarget()
        url = target.get_url(temp_package_json_scoped)
        assert url == "https://www.jsdelivr.com/package/npm/@myorg/test-project"

    def test_unpkg_target(self, temp_package_json: str) -> None:
        target = UnpkgTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://unpkg.com/test-project"

    def test_unpkg_target_no_config(self, temp_dir: str) -> None:
        target = UnpkgTarget()
        with pytest.raises(ProjectMetadataError, match="No package.json found"):
            target.get_url(temp_dir)

    def test_unpkg_target_scoped(self, temp_package_json_scoped: str) -> None:
        target = UnpkgTarget()
        url = target.get_url(temp_package_json_scoped)
        assert url == "https://unpkg.com/@myorg/test-project"

    def test_skypack_target(self, temp_package_json: str) -> None:
        target = SkypackTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://www.skypack.dev/view/test-project"

    def test_skypack_target_no_config(self, temp_dir: str) -> None:
        target = SkypackTarget()
        with pytest.raises(ProjectMetadataError, match="No package.json found"):
            target.get_url(temp_dir)

    def test_skypack_target_scoped(self, temp_package_json_scoped: str) -> None:
        target = SkypackTarget()
        url = target.get_url(temp_package_json_scoped)
        assert url == "https://www.skypack.dev/view/@myorg/test-project"

    def test_open_vsx_target(self, temp_open_vsx_package_json: str) -> None:
        target = OpenVSXTarget()
        url = target.get_url(temp_open_vsx_package_json)
        assert url == "https://open-vsx.org/extension/testpublisher/test-extension"

    def test_open_vsx_target_no_config(self, temp_dir: str) -> None:
        target = OpenVSXTarget()
        with pytest.raises(ProjectMetadataError, match="No package.json found"):
            target.get_url(temp_dir)

    def test_open_vsx_target_missing_publisher(self, temp_package_json: str) -> None:
        target = OpenVSXTarget()
        with pytest.raises(ProjectMetadataError, match="No 'publisher' in package.json"):
            target.get_url(temp_package_json)

    def test_maven_target(self, temp_maven_pom: str) -> None:
        target = MavenTarget()
        url = target.get_url(temp_maven_pom)
        assert url == "https://central.sonatype.com/artifact/com.example/test-app"

    def test_maven_target_no_config(self, temp_dir: str) -> None:
        target = MavenTarget()
        with pytest.raises(ProjectMetadataError, match="No pom.xml found"):
            target.get_url(temp_dir)

    def test_maven_target_invalid_xml(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text("<project><groupId>com.example", encoding="utf-8")
        target = MavenTarget()
        with pytest.raises(ProjectMetadataError, match="Invalid pom.xml"):
            target.get_url(str(tmp_path))

    def test_maven_target_parent_group_id(self, tmp_path: Path) -> None:
        pom = tmp_path / "pom.xml"
        pom.write_text(
            '<?xml version="1.0"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            "  <parent>\n"
            "    <groupId>com.parent</groupId>\n"
            "    <artifactId>parent-app</artifactId>\n"
            "    <version>1.0.0</version>\n"
            "  </parent>\n"
            "  <artifactId>child-app</artifactId>\n"
            "</project>\n",
            encoding="utf-8",
        )
        target = MavenTarget()
        url = target.get_url(str(tmp_path))
        assert url == "https://central.sonatype.com/artifact/com.parent/child-app"

    def test_maven_target_grandparent_group_id(self, tmp_path: Path) -> None:
        """groupId resolved via two-level parent chain (parent has no groupId either)."""
        grandparent = tmp_path / "grandparent"
        parent = tmp_path / "parent"
        child = tmp_path / "child"
        grandparent.mkdir()
        parent.mkdir()
        child.mkdir()

        (grandparent / "pom.xml").write_text(
            '<?xml version="1.0"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            "  <groupId>com.corp</groupId>\n"
            "  <artifactId>corp-bom</artifactId>\n"
            "  <version>1.0.0</version>\n"
            "</project>\n",
            encoding="utf-8",
        )
        (parent / "pom.xml").write_text(
            '<?xml version="1.0"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            "  <parent>\n"
            "    <artifactId>corp-bom</artifactId>\n"
            "    <version>1.0.0</version>\n"
            "    <relativePath>../grandparent/pom.xml</relativePath>\n"
            "  </parent>\n"
            "  <artifactId>product-parent</artifactId>\n"
            "</project>\n",
            encoding="utf-8",
        )
        (child / "pom.xml").write_text(
            '<?xml version="1.0"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            "  <parent>\n"
            "    <artifactId>product-parent</artifactId>\n"
            "    <version>1.0.0</version>\n"
            "    <relativePath>../parent/pom.xml</relativePath>\n"
            "  </parent>\n"
            "  <artifactId>service-app</artifactId>\n"
            "</project>\n",
            encoding="utf-8",
        )

        target = MavenTarget()
        url = target.get_url(str(child))
        assert url == "https://central.sonatype.com/artifact/com.corp/service-app"

    def test_maven_target_no_group_in_chain(self, tmp_path: Path) -> None:
        """No groupId anywhere in chain raises ProjectMetadataError."""
        pom = tmp_path / "pom.xml"
        pom.write_text(
            '<?xml version="1.0"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
            "  <artifactId>orphan-app</artifactId>\n"
            "</project>\n",
            encoding="utf-8",
        )
        target = MavenTarget()
        with pytest.raises(ProjectMetadataError, match="No 'groupId'"):
            target.get_url(str(tmp_path))

    def test_hackage_target(self, temp_hackage_cabal: str) -> None:
        target = HackageTarget()
        url = target.get_url(temp_hackage_cabal)
        assert url == "https://hackage.haskell.org/package/test-package"

    def test_hackage_target_no_config(self, temp_dir: str) -> None:
        target = HackageTarget()
        with pytest.raises(ProjectMetadataError, match="No .cabal file found"):
            target.get_url(temp_dir)

    def test_hackage_target_missing_name(self, tmp_path: Path) -> None:
        cabal = tmp_path / "test-package.cabal"
        cabal.write_text(
            "cabal-version: >=1.10\nversion: 0.1.0.0\nbuild-type: Simple\n",
            encoding="utf-8",
        )
        target = HackageTarget()
        with pytest.raises(ProjectMetadataError, match="No 'name' in .cabal file"):
            target.get_url(str(tmp_path))

    def test_cpan_target(self, temp_cpanfile: str) -> None:
        target = CpanTarget()
        url = target.get_url(temp_cpanfile)
        assert url == "https://metacpan.org/pod/Test%3A%3AProject"

    def test_cpan_target_no_config(self, temp_dir: str) -> None:
        target = CpanTarget()
        with pytest.raises(ProjectMetadataError, match="Could not determine CPAN module name"):
            target.get_url(temp_dir)

    def test_cpan_target_dist_ini_only(self, tmp_path: Path) -> None:
        dist_ini = tmp_path / "dist.ini"
        dist_ini.write_text("name = My-Module\nversion = 0.001\n", encoding="utf-8")
        target = CpanTarget()
        url = target.get_url(str(tmp_path))
        assert url == "https://metacpan.org/pod/My%3A%3AModule"

    def test_cpan_target_lib_layout(self, tmp_path: Path) -> None:
        lib_dir = tmp_path / "lib" / "Foo"
        lib_dir.mkdir(parents=True)
        (tmp_path / "lib" / "Foo.pm").write_text("package Foo;\n1;\n", encoding="utf-8")
        (lib_dir / "Bar.pm").write_text("package Foo::Bar;\n1;\n", encoding="utf-8")
        target = CpanTarget()
        url = target.get_url(str(tmp_path))
        # Should prefer shallowest module (Foo) over deeper (Foo::Bar)
        assert url == "https://metacpan.org/pod/Foo"

    def test_cpan_target_lib_wins_over_dist_ini(self, tmp_path: Path) -> None:
        """When dist hyphen-name would mislead, lib/ layout takes precedence.

        Distribution `Foo-Bar` containing single module `FooBar.pm` should resolve
        to `FooBar`, not the heuristic `Foo::Bar` from dist.ini.
        """
        (tmp_path / "dist.ini").write_text("name = Foo-Bar\nversion = 0.001\n", encoding="utf-8")
        lib_dir = tmp_path / "lib"
        lib_dir.mkdir()
        (lib_dir / "FooBar.pm").write_text("package FooBar;\n1;\n", encoding="utf-8")
        target = CpanTarget()
        url = target.get_url(str(tmp_path))
        assert url == "https://metacpan.org/pod/FooBar"


class TestMultiEcosystemTargets:
    """Tests for multi-ecosystem target suffix notation."""

    def test_snyk_is_multi_ecosystem(self) -> None:
        assert issubclass(SnykTarget, MultiEcosystemTarget)

    def test_snyk_supported_ecosystems(self) -> None:
        expected = {"pypi", "npm", "go", "cargo"}
        assert set(SnykTarget.ecosystem_url_map.keys()) == expected

    def test_snyk_auto_detect_single_ecosystem(self, temp_pyproject: str) -> None:
        target = SnykTarget()
        url = target.get_url(temp_pyproject)
        assert url == "https://snyk.io/advisor/python/test-project"

    def test_snyk_explicit_ecosystem_suffix(self, temp_pyproject: str) -> None:
        target = SnykTarget(ecosystem="pypi")
        url = target.get_url(temp_pyproject)
        assert url == "https://snyk.io/advisor/python/test-project"

    def test_snyk_npm_ecosystem(self, temp_package_json: str) -> None:
        target = SnykTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://snyk.io/advisor/npm-package/test-project"

    def test_snyk_cargo_ecosystem(self, temp_cargo_toml: str) -> None:
        target = SnykTarget()
        url = target.get_url(temp_cargo_toml)
        assert url == "https://snyk.io/advisor/rust/test-crate"

    def test_snyk_go_ecosystem(self, temp_go_mod: str) -> None:
        target = SnykTarget()
        url = target.get_url(temp_go_mod)
        assert url == "https://snyk.io/advisor/golang/github.com/testuser/test-go-module"

    def test_socket_npm_ecosystem(self, temp_package_json: str) -> None:
        target = SocketTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://socket.dev/npm/package/test-project"

    def test_socket_pypi_ecosystem(self, temp_pyproject: str) -> None:
        target = SocketTarget()
        url = target.get_url(temp_pyproject)
        assert url == "https://socket.dev/pypi/package/test-project"

    def test_socket_cargo_ecosystem(self, temp_cargo_toml: str) -> None:
        target = SocketTarget()
        url = target.get_url(temp_cargo_toml)
        assert url == "https://socket.dev/cargo/package/test-crate"

    def test_socket_go_ecosystem(self, temp_go_mod: str) -> None:
        target = SocketTarget()
        url = target.get_url(temp_go_mod)
        assert url == "https://socket.dev/go/package/github.com/testuser/test-go-module"

    def test_socket_suffix_npm(self, temp_package_json: str) -> None:
        target = get_target("socket:npm")
        assert isinstance(target, SocketTarget)
        url = target.get_url(temp_package_json)
        assert url == "https://socket.dev/npm/package/test-project"

    def test_socket_suffix_pypi(self, temp_pyproject: str) -> None:
        target = get_target("socket:pypi")
        assert isinstance(target, SocketTarget)
        url = target.get_url(temp_pyproject)
        assert url == "https://socket.dev/pypi/package/test-project"

    def test_snyk_multi_ecosystem_error(self, temp_multi_ecosystem: str) -> None:
        target = SnykTarget()
        with pytest.raises(ProjectMetadataError) as exc_info:
            target.get_url(temp_multi_ecosystem)
        assert "Multiple ecosystems detected" in str(exc_info.value)
        assert "snyk:npm" in str(exc_info.value)
        assert "snyk:pypi" in str(exc_info.value)

    def test_snyk_explicit_in_multi_ecosystem(self, temp_multi_ecosystem: str) -> None:
        target = SnykTarget(ecosystem="pypi")
        url = target.get_url(temp_multi_ecosystem)
        assert url == "https://snyk.io/advisor/python/multi-project"

    def test_snyk_invalid_ecosystem(self, temp_pyproject: str) -> None:
        target = SnykTarget(ecosystem="invalid")
        with pytest.raises(ProjectMetadataError) as exc_info:
            target.get_url(temp_pyproject)
        assert "doesn't support ecosystem 'invalid'" in str(exc_info.value)

    def test_deps_dev_pypi(self, temp_pyproject: str) -> None:
        target = DepsDevTarget()
        url = target.get_url(temp_pyproject)
        assert url == "https://deps.dev/pypi/test-project"

    def test_deps_dev_npm(self, temp_package_json: str) -> None:
        target = DepsDevTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://deps.dev/npm/test-project"

    def test_libraries_io_pypi(self, temp_pyproject: str) -> None:
        target = LibrariesIOTarget()
        url = target.get_url(temp_pyproject)
        assert url == "https://libraries.io/pypi/test-project"

    def test_libraries_io_npm(self, temp_package_json: str) -> None:
        target = LibrariesIOTarget()
        url = target.get_url(temp_package_json)
        assert url == "https://libraries.io/npm/test-project"

    def test_get_target_with_suffix(self) -> None:
        target = get_target("snyk:pypi")
        assert isinstance(target, SnykTarget)
        assert target._ecosystem == "pypi"

    def test_get_target_without_suffix(self) -> None:
        target = get_target("snyk")
        assert isinstance(target, SnykTarget)
        assert target._ecosystem is None

    def test_get_target_suffix_on_non_multi_ecosystem_fails(self) -> None:
        with pytest.raises(UnknownTargetError) as exc_info:
            get_target("pypi:something")
        assert "doesn't support ecosystem suffix" in str(exc_info.value)

    def test_multi_ecosystem_no_supported_ecosystem(self, temp_dir: str) -> None:
        target = SnykTarget()
        with pytest.raises(ProjectMetadataError) as exc_info:
            target.get_url(temp_dir)
        assert "No supported ecosystem found" in str(exc_info.value)

    @pytest.mark.parametrize(
        "target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget, SocketTarget]
    )
    def test_multi_ecosystem_auto_detect_pypi(
        self, target_cls: type[MultiEcosystemTarget], temp_pyproject: str
    ) -> None:
        target = target_cls()
        url = target.get_url(temp_pyproject)
        assert "test-project" in url

    @pytest.mark.parametrize(
        "target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget, SocketTarget]
    )
    def test_multi_ecosystem_auto_detect_npm(
        self, target_cls: type[MultiEcosystemTarget], temp_package_json: str
    ) -> None:
        target = target_cls()
        url = target.get_url(temp_package_json)
        assert "test-project" in url

    @pytest.mark.parametrize(
        "target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget, SocketTarget]
    )
    def test_multi_ecosystem_auto_detect_cargo(
        self, target_cls: type[MultiEcosystemTarget], temp_cargo_toml: str
    ) -> None:
        target = target_cls()
        url = target.get_url(temp_cargo_toml)
        assert "test-crate" in url

    @pytest.mark.parametrize(
        "target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget, SocketTarget]
    )
    def test_multi_ecosystem_auto_detect_go(
        self, target_cls: type[MultiEcosystemTarget], temp_go_mod: str
    ) -> None:
        target = target_cls()
        url = target.get_url(temp_go_mod)
        assert "test-go-module" in url

    @pytest.mark.parametrize(
        "raw_target",
        ["libraries-io:foo", "deps:foo", "ecosystems:foo", "socket:foo"],
    )
    def test_multi_ecosystem_invalid_suffix_raises(self, raw_target: str) -> None:
        with pytest.raises(UnknownTargetError) as exc_info:
            get_target(raw_target)
        assert "doesn't support ecosystem 'foo'" in str(exc_info.value)


class TestServiceTargets:
    """Tests for Codecov and Coveralls service targets."""

    def test_codecov_target_github(self, temp_git_repo: str) -> None:
        target = CodecovTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://codecov.io/gh/testuser/testrepo"

    def test_codecov_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = CodecovTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://codecov.io/gl/testuser/testrepo"

    def test_codecov_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = CodecovTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://codecov.io/bb/testuser/testrepo"

    def test_coveralls_target_github(self, temp_git_repo: str) -> None:
        target = CoverallsTarget()
        url = target.get_url(temp_git_repo)
        assert url == "https://coveralls.io/github/testuser/testrepo"

    def test_coveralls_target_gitlab(self, temp_git_repo_gitlab: str) -> None:
        target = CoverallsTarget()
        url = target.get_url(temp_git_repo_gitlab)
        assert url == "https://coveralls.io/gitlab/testuser/testrepo"

    def test_coveralls_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = CoverallsTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url == "https://coveralls.io/bitbucket/testuser/testrepo"

    def test_codecov_target_gitea_unsupported(self, temp_git_repo_gitea: str) -> None:
        """Codecov has no gitea integration — must raise, not emit a 404 URL."""
        target = CodecovTarget()
        with pytest.raises(UnsupportedFeatureError, match="does not support 'gitea'"):
            target.get_url(temp_git_repo_gitea)

    def test_codecov_target_forgejo_unsupported(self, temp_git_repo_forgejo: str) -> None:
        target = CodecovTarget()
        with pytest.raises(UnsupportedFeatureError, match="does not support 'forgejo'"):
            target.get_url(temp_git_repo_forgejo)

    def test_coveralls_target_gitea_unsupported(self, temp_git_repo_gitea: str) -> None:
        target = CoverallsTarget()
        with pytest.raises(UnsupportedFeatureError, match="does not support 'gitea'"):
            target.get_url(temp_git_repo_gitea)

    def test_coveralls_target_forgejo_unsupported(self, temp_git_repo_forgejo: str) -> None:
        target = CoverallsTarget()
        with pytest.raises(UnsupportedFeatureError, match="does not support 'forgejo'"):
            target.get_url(temp_git_repo_forgejo)


class TestRegistryURLCoverage:
    """One assertion per remaining target so URL drift surfaces in CI."""

    def test_inspector(self, temp_pyproject: str) -> None:
        assert (
            InspectorTarget().get_url(temp_pyproject)
            == "https://inspector.pypi.io/project/test-project/"
        )

    def test_pypi_json(self, temp_pyproject: str) -> None:
        assert PyPIJSONTarget().get_url(temp_pyproject) == "https://pypi.org/pypi/test-project/json"

    def test_pepy(self, temp_pyproject: str) -> None:
        assert PePyTarget().get_url(temp_pyproject) == "https://www.pepy.tech/projects/test-project"

    def test_pypistats(self, temp_pyproject: str) -> None:
        assert (
            PyPIStatsTarget().get_url(temp_pyproject)
            == "https://pypistats.org/packages/test-project"
        )

    def test_piptrends(self, temp_pyproject: str) -> None:
        assert (
            PipTrendsTarget().get_url(temp_pyproject)
            == "https://piptrends.com/package/test-project"
        )

    def test_clickpy(self, temp_pyproject: str) -> None:
        assert (
            ClickPyTarget().get_url(temp_pyproject)
            == "https://clickpy.clickhouse.com/dashboard/test-project"
        )

    def test_safety_db(self, temp_pyproject: str) -> None:
        assert (
            SafetyDBTarget().get_url(temp_pyproject)
            == "https://data.safetycli.com/packages/pypi/test-project"
        )

    def test_bundlephobia(self, temp_package_json: str) -> None:
        assert (
            BundlephobiaTarget().get_url(temp_package_json)
            == "https://bundlephobia.com/package/test-project"
        )

    def test_packagephobia(self, temp_package_json: str) -> None:
        assert (
            PackagephobiaTarget().get_url(temp_package_json)
            == "https://packagephobia.com/result?p=test-project"
        )

    def test_packagephobia_scoped_encoded(self, temp_package_json_scoped: str) -> None:
        """Scoped names must round-trip through urlencode (`@` → `%40`, `/` → `%2F`)."""
        url = PackagephobiaTarget().get_url(temp_package_json_scoped)
        assert url == "https://packagephobia.com/result?p=%40myorg%2Ftest-project"

    def test_npm_stat(self, temp_package_json: str) -> None:
        assert (
            NPMStatTarget().get_url(temp_package_json)
            == "https://npm-stat.com/charts.html?package=test-project"
        )

    def test_npm_stat_scoped_encoded(self, temp_package_json_scoped: str) -> None:
        url = NPMStatTarget().get_url(temp_package_json_scoped)
        assert url == "https://npm-stat.com/charts.html?package=%40myorg%2Ftest-project"

    def test_librs(self, temp_cargo_toml: str) -> None:
        assert LibRsTarget().get_url(temp_cargo_toml) == "https://lib.rs/crates/test-crate"

    def test_packagist_target_no_config(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError, match="No composer.json found"):
            PackagistTarget().get_url(temp_dir)

    def test_pub_target_no_config(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError, match="No pubspec.yaml found"):
            PubTarget().get_url(temp_dir)

    def test_hex_target_no_config(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError, match="No mix.exs found"):
            HexTarget().get_url(temp_dir)

    def test_nuget_target_no_config(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError, match="No .csproj file found"):
            NuGetTarget().get_url(temp_dir)


class TestRegistryDriftGuard:
    """Guard against REGISTRY ↔ targets module drift."""

    def test_registry_keys_match_target_classes(self) -> None:
        """Every Target subclass with a `name` should be in REGISTRY (or a base)."""
        from olink.core import targets as targets_mod
        from olink.core.targets import Target

        target_subclasses = {
            cls
            for _, cls in vars(targets_mod).items()
            if isinstance(cls, type) and issubclass(cls, Target) and cls is not Target
        }
        # Skip abstract bases (no `name` ClassVar set on the class itself).
        concrete = {cls for cls in target_subclasses if "name" in cls.__dict__}
        registered_classes = set(REGISTRY.values())
        missing = concrete - registered_classes
        assert missing == set(), f"Target classes defined but not in REGISTRY: {missing}"
