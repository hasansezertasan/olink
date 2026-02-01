"""Tests for git.py - Git operations, URL parsing, and project metadata."""

import json
from pathlib import Path

import pytest

from olink.core.exceptions import NotGitRepoError, ProjectMetadataError, UnknownPlatformError
from olink.core.project import (
    ParsedRemote,
    detect_ecosystems,
    get_package_name,
    get_remote_url,
    parse_remote_url,
)


class TestParseRemoteUrl:
    """Tests for parse_remote_url function."""

    def test_parse_github_ssh(self) -> None:
        url = "git@github.com:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "github"
        assert result.host == "github.com"
        assert result.owner == "owner"
        assert result.repo == "repo"
        assert result.base_url == "https://github.com/owner/repo"

    def test_parse_github_ssh_without_git_suffix(self) -> None:
        url = "git@github.com:owner/repo"
        result = parse_remote_url(url)
        assert result.platform == "github"
        assert result.repo == "repo"

    def test_parse_gitlab_ssh(self) -> None:
        url = "git@gitlab.com:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "gitlab"
        assert result.host == "gitlab.com"
        assert result.owner == "owner"
        assert result.repo == "repo"

    def test_parse_bitbucket_ssh(self) -> None:
        url = "git@bitbucket.org:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "bitbucket"
        assert result.host == "bitbucket.org"

    def test_parse_github_https(self) -> None:
        url = "https://github.com/owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "github"
        assert result.host == "github.com"
        assert result.owner == "owner"
        assert result.repo == "repo"

    def test_parse_github_https_without_git_suffix(self) -> None:
        url = "https://github.com/owner/repo"
        result = parse_remote_url(url)
        assert result.platform == "github"
        assert result.repo == "repo"

    def test_parse_gitlab_https(self) -> None:
        url = "https://gitlab.com/owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "gitlab"

    def test_parse_bitbucket_https(self) -> None:
        url = "https://bitbucket.org/owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "bitbucket"

    def test_parse_git_protocol(self) -> None:
        url = "git://github.com/owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "github"
        assert result.host == "github.com"

    def test_parse_self_hosted_gitlab(self) -> None:
        url = "git@gitlab.mycompany.com:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "gitlab"
        assert result.host == "gitlab.mycompany.com"

    def test_parse_self_hosted_github_enterprise(self) -> None:
        url = "git@github.mycompany.com:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "github"

    def test_parse_unknown_platform_raises(self) -> None:
        url = "git@unknown.com:owner/repo.git"
        with pytest.raises(UnknownPlatformError, match="Unknown git hosting platform"):
            parse_remote_url(url)

    def test_parse_invalid_url_raises(self) -> None:
        url = "not-a-valid-url"
        with pytest.raises(UnknownPlatformError, match="Could not parse remote URL"):
            parse_remote_url(url)

    def test_parse_repo_with_dots(self) -> None:
        url = "git@github.com:owner/my.repo.name.git"
        result = parse_remote_url(url)
        assert result.repo == "my.repo.name"

    def test_parse_repo_with_hyphens(self) -> None:
        url = "git@github.com:my-org/my-repo.git"
        result = parse_remote_url(url)
        assert result.owner == "my-org"
        assert result.repo == "my-repo"


class TestGetRemoteUrl:
    """Tests for get_remote_url function."""

    def test_get_remote_url_origin(self, temp_git_repo: str) -> None:
        url = get_remote_url(temp_git_repo, "origin")
        assert url == "git@github.com:testuser/testrepo.git"

    def test_get_remote_url_nonexistent(self, temp_git_repo: str) -> None:
        url = get_remote_url(temp_git_repo, "nonexistent")
        assert url is None

    def test_get_remote_url_not_git_repo(self, temp_dir: str) -> None:
        with pytest.raises(NotGitRepoError):
            get_remote_url(temp_dir, "origin")


class TestParsedRemote:
    """Tests for ParsedRemote dataclass."""

    def test_base_url_property(self) -> None:
        remote = ParsedRemote(
            platform="github",
            host="github.com",
            owner="testowner",
            repo="testrepo",
        )
        assert remote.base_url == "https://github.com/testowner/testrepo"


class TestDetectEcosystems:
    """Tests for detect_ecosystems function."""

    def test_detect_python(self, temp_pyproject: str) -> None:
        ecosystems = detect_ecosystems(temp_pyproject)
        assert "pypi" in ecosystems

    def test_detect_npm(self, temp_package_json: str) -> None:
        ecosystems = detect_ecosystems(temp_package_json)
        assert "npm" in ecosystems

    def test_detect_cargo(self, temp_cargo_toml: str) -> None:
        ecosystems = detect_ecosystems(temp_cargo_toml)
        assert "cargo" in ecosystems

    def test_detect_go(self, temp_go_mod: str) -> None:
        ecosystems = detect_ecosystems(temp_go_mod)
        assert "go" in ecosystems

    def test_detect_multi_ecosystem(self, temp_multi_ecosystem: str) -> None:
        ecosystems = detect_ecosystems(temp_multi_ecosystem)
        assert "pypi" in ecosystems
        assert "npm" in ecosystems

    def test_detect_empty_dir(self, temp_dir: str) -> None:
        ecosystems = detect_ecosystems(temp_dir)
        assert ecosystems == []

    def test_detect_skips_invalid_metadata_with_warning(self, temp_dir: str, caplog: pytest.LogCaptureFixture) -> None:
        # pyproject.toml without [project].name
        Path(temp_dir, "pyproject.toml").write_text("[project]\nversion = '1.0'\n")
        import logging

        with caplog.at_level(logging.WARNING):
            ecosystems = detect_ecosystems(temp_dir)
        assert "pypi" not in ecosystems
        assert any("skipped" in r.message.lower() for r in caplog.records)


class TestGetPackageName:
    """Tests for get_package_name function."""

    def test_python_package_name(self, temp_pyproject: str) -> None:
        assert get_package_name(temp_pyproject, "pypi") == "test-project"

    def test_npm_package_name(self, temp_package_json: str) -> None:
        assert get_package_name(temp_package_json, "npm") == "test-project"

    def test_cargo_package_name(self, temp_cargo_toml: str) -> None:
        assert get_package_name(temp_cargo_toml, "cargo") == "test-crate"

    def test_go_package_name(self, temp_go_mod: str) -> None:
        assert get_package_name(temp_go_mod, "go") == "github.com/testuser/test-go-module"

    def test_unknown_ecosystem_raises(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError, match="Unknown ecosystem"):
            get_package_name(temp_dir, "unknown")

    def test_missing_pyproject_raises(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError):
            get_package_name(temp_dir, "pypi")

    def test_missing_package_json_raises(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError):
            get_package_name(temp_dir, "npm")

    def test_missing_cargo_toml_raises(self, temp_dir: str) -> None:
        with pytest.raises(ProjectMetadataError):
            get_package_name(temp_dir, "cargo")

    def test_malformed_pyproject_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "pyproject.toml").write_text("[project]\nversion = '1.0'\n")
        with pytest.raises(ProjectMetadataError):
            get_package_name(temp_dir, "pypi")

    def test_malformed_package_json_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "package.json").write_text(json.dumps({"version": "1.0"}))
        with pytest.raises(ProjectMetadataError):
            get_package_name(temp_dir, "npm")
