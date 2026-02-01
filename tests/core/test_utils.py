"""Tests for git.py - Git operations and URL parsing."""

import pytest

from olink.core.exceptions import NotGitRepoError, UnknownPlatformError
from olink.core.project import (
    ParsedRemote,
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
