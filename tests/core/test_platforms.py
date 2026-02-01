"""Tests for platform URL generation."""

import pytest

from olink.core.exceptions import UnknownPlatformError
from olink.core.targets import PLATFORM_URLS, get_platform_url


class TestPlatformUrls:
    """Tests for PLATFORM_URLS dict."""

    def test_github_urls(self) -> None:
        assert PLATFORM_URLS["github"]["issues"] == "/issues"
        assert PLATFORM_URLS["github"]["pulls"] == "/pulls"
        assert PLATFORM_URLS["github"]["actions"] == "/actions"

    def test_gitlab_urls(self) -> None:
        assert PLATFORM_URLS["gitlab"]["issues"] == "/-/issues"
        assert PLATFORM_URLS["gitlab"]["pulls"] == "/-/merge_requests"
        assert PLATFORM_URLS["gitlab"]["actions"] == "/-/pipelines"

    def test_bitbucket_urls(self) -> None:
        assert PLATFORM_URLS["bitbucket"]["issues"] == "/issues"
        assert PLATFORM_URLS["bitbucket"]["pulls"] == "/pull-requests"
        assert PLATFORM_URLS["bitbucket"]["actions"] == "/pipelines"


class TestGetPlatformUrl:
    """Tests for get_platform_url function."""

    def test_github_issues(self) -> None:
        url = get_platform_url("https://github.com/owner/repo", "github", "issues")
        assert url == "https://github.com/owner/repo/issues"

    def test_github_pulls(self) -> None:
        url = get_platform_url("https://github.com/owner/repo", "github", "pulls")
        assert url == "https://github.com/owner/repo/pulls"

    def test_github_actions(self) -> None:
        url = get_platform_url("https://github.com/owner/repo", "github", "actions")
        assert url == "https://github.com/owner/repo/actions"

    def test_gitlab_issues(self) -> None:
        url = get_platform_url("https://gitlab.com/owner/repo", "gitlab", "issues")
        assert url == "https://gitlab.com/owner/repo/-/issues"

    def test_gitlab_pulls(self) -> None:
        url = get_platform_url("https://gitlab.com/owner/repo", "gitlab", "pulls")
        assert url == "https://gitlab.com/owner/repo/-/merge_requests"

    def test_gitlab_actions(self) -> None:
        url = get_platform_url("https://gitlab.com/owner/repo", "gitlab", "actions")
        assert url == "https://gitlab.com/owner/repo/-/pipelines"

    def test_bitbucket_issues(self) -> None:
        url = get_platform_url("https://bitbucket.org/owner/repo", "bitbucket", "issues")
        assert url == "https://bitbucket.org/owner/repo/issues"

    def test_bitbucket_pulls(self) -> None:
        url = get_platform_url("https://bitbucket.org/owner/repo", "bitbucket", "pulls")
        assert url == "https://bitbucket.org/owner/repo/pull-requests"

    def test_bitbucket_actions(self) -> None:
        url = get_platform_url("https://bitbucket.org/owner/repo", "bitbucket", "actions")
        assert url == "https://bitbucket.org/owner/repo/pipelines"

    def test_unknown_platform_raises(self) -> None:
        with pytest.raises(UnknownPlatformError):
            get_platform_url("https://example.com/owner/repo", "unknown", "issues")
