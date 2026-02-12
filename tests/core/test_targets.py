"""Tests for targets/ - Target URL generation."""

import subprocess

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
    CodecovTarget,
    CommitsTarget,
    CoverallsTarget,
    CratesTarget,
    DepsDevTarget,
    DiscussionsTarget,
    EcosystemsTarget,
    GemsTarget,
    IssuesTarget,
    LibrariesIOTarget,
    MultiEcosystemTarget,
    NPMTarget,
    OriginTarget,
    PullsTarget,
    ReleasesTarget,
    SecurityTarget,
    WikiTarget,
    PiWheelsTarget,
    PyPITarget,
    SnykTarget,
    UpstreamTarget,
)


class TestRegistry:
    """Tests for target registry."""

    def test_all_targets_registered(self) -> None:
        expected_targets = {
            "origin", "upstream", "issues", "pulls", "actions", "wiki",
            "releases", "branches", "commits", "security", "discussions",
            "pypi", "inspector", "pypi-json", "pepy", "piwheels", "pypistats",
            "piptrends", "clickpy", "snyk", "safety-db",
            "libraries-io", "deps", "ecosystems",
            "npm", "bundlephobia", "packagephobia", "npm-stat",
            "crates", "librs",
            "gems", "packagist", "pub", "hex", "nuget",
            "codecov", "coveralls",
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

    @pytest.mark.parametrize("target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget])
    def test_multi_ecosystem_auto_detect_pypi(self, target_cls: type[MultiEcosystemTarget], temp_pyproject: str) -> None:
        target = target_cls()
        url = target.get_url(temp_pyproject)
        assert "test-project" in url

    @pytest.mark.parametrize("target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget])
    def test_multi_ecosystem_auto_detect_npm(self, target_cls: type[MultiEcosystemTarget], temp_package_json: str) -> None:
        target = target_cls()
        url = target.get_url(temp_package_json)
        assert "test-project" in url

    @pytest.mark.parametrize("target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget])
    def test_multi_ecosystem_auto_detect_cargo(self, target_cls: type[MultiEcosystemTarget], temp_cargo_toml: str) -> None:
        target = target_cls()
        url = target.get_url(temp_cargo_toml)
        assert "test-crate" in url

    @pytest.mark.parametrize("target_cls", [LibrariesIOTarget, DepsDevTarget, EcosystemsTarget])
    def test_multi_ecosystem_auto_detect_go(self, target_cls: type[MultiEcosystemTarget], temp_go_mod: str) -> None:
        target = target_cls()
        url = target.get_url(temp_go_mod)
        assert "test-go-module" in url

    @pytest.mark.parametrize(
        "raw_target",
        ["libraries-io:foo", "deps:foo", "ecosystems:foo"],
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
        assert url.startswith("https://coveralls.io/")
        assert "testuser" in url
        assert "testrepo" in url

    def test_coveralls_target_bitbucket(self, temp_git_repo_bitbucket: str) -> None:
        target = CoverallsTarget()
        url = target.get_url(temp_git_repo_bitbucket)
        assert url.startswith("https://coveralls.io/")
        assert "testuser" in url
        assert "testrepo" in url
