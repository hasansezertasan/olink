"""Tests for project.py - Git operations, URL parsing, and project metadata."""

import json
import os
import sys
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

    def test_parse_gitea_host(self) -> None:
        url = "git@gitea.example.com:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "gitea"

    def test_parse_forgejo_host(self) -> None:
        url = "git@forgejo.example.com:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "forgejo"

    def test_parse_codeberg_host(self) -> None:
        url = "git@codeberg.org:owner/repo.git"
        result = parse_remote_url(url)
        assert result.platform == "forgejo"

    def test_parse_gitea_https(self) -> None:
        result = parse_remote_url("https://gitea.example.com/owner/repo.git")
        assert result.platform == "gitea"
        assert result.host == "gitea.example.com"

    def test_parse_forgejo_https(self) -> None:
        result = parse_remote_url("https://forgejo.example.com/owner/repo.git")
        assert result.platform == "forgejo"

    def test_parse_codeberg_https(self) -> None:
        result = parse_remote_url("https://codeberg.org/owner/repo")
        assert result.platform == "forgejo"
        assert result.host == "codeberg.org"

    def test_parse_ssh_with_port_unsupported(self) -> None:
        """`ssh://git@host:22/owner/repo.git` form is currently unsupported.

        Documented refusal — not a panic. If/when port-form is added, switch to
        a positive assertion.
        """
        with pytest.raises(UnknownPlatformError):
            parse_remote_url("ssh://git@github.com:22/owner/repo.git")

    def test_parse_no_substring_false_positive(self) -> None:
        """Hostname `gitlabby.example.com` must NOT match the `gitlab` keyword.

        Earlier substring-based detection wrongly classified arbitrary hosts;
        label-based detection rejects them.
        """
        with pytest.raises(UnknownPlatformError):
            parse_remote_url("git@gitlabby.example.com:owner/repo.git")
        with pytest.raises(UnknownPlatformError):
            parse_remote_url("git@mygiteahome.io:owner/repo.git")
        with pytest.raises(UnknownPlatformError):
            parse_remote_url("git@notforgejostuff.dev:owner/repo.git")


class TestInsteadOfRewrites:
    """Tests for [url].insteadOf rewriting in get_remote_url."""

    def test_insteadof_rewrite_applied(self, temp_dir: str) -> None:
        """SSH alias rewrite resolves to canonical github URL."""
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.write_text(
            config.read_text()
            + '\n[remote "origin"]\n'
            + "\turl = github:owner/repo.git\n"
            + '[url "git@github.com:"]\n'
            + "\tinsteadOf = github:\n"
        )
        url = get_remote_url(temp_dir, "origin")
        assert url == "git@github.com:owner/repo.git"

    def test_insteadof_longest_match_wins(self, temp_dir: str) -> None:
        """When two insteadOf rules match, the longer prefix wins (matches git behavior)."""
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.write_text(
            config.read_text()
            + '\n[remote "origin"]\n'
            + "\turl = work:repo.git\n"
            + '[url "git@gitlab.com:"]\n'
            + "\tinsteadOf = w:\n"
            + '[url "git@github.com:owner/"]\n'
            + "\tinsteadOf = work:\n"
        )
        url = get_remote_url(temp_dir, "origin")
        assert url == "git@github.com:owner/repo.git"

    def test_insteadof_multiple_per_section(self, temp_dir: str) -> None:
        """Multiple insteadOf lines in one [url "..."] section all become rewrite rules."""
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.write_text(
            config.read_text()
            + '\n[remote "origin"]\n'
            + "\turl = github:owner/repo.git\n"
            + '[url "git@github.com:"]\n'
            + "\tinsteadOf = github:\n"
            + "\tinsteadOf = gh:\n"
        )
        # First alias matches
        assert get_remote_url(temp_dir, "origin") == "git@github.com:owner/repo.git"
        # Second alias also rewrites — write new remote using gh: prefix
        config.write_text(
            config.read_text().replace(
                "url = github:owner/repo.git", "url = gh:owner/repo.git"
            )
        )
        assert get_remote_url(temp_dir, "origin") == "git@github.com:owner/repo.git"

    def test_insteadof_strips_trailing_comment(self, temp_dir: str) -> None:
        """`insteadOf = github: # alias` should not capture ` # alias` in the prefix."""
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.write_text(
            config.read_text()
            + '\n[remote "origin"]\n'
            + "\turl = github:owner/repo.git\n"
            + '[url "git@github.com:"]\n'
            + "\tinsteadOf = github: # personal alias\n"
        )
        url = get_remote_url(temp_dir, "origin")
        assert url == "git@github.com:owner/repo.git"

    def test_insteadof_no_match_returns_raw(self, temp_dir: str) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.write_text(
            config.read_text()
            + '\n[remote "origin"]\n'
            + "\turl = git@github.com:owner/repo.git\n"
            + '[url "https://nope/"]\n'
            + "\tinsteadOf = unrelated:\n"
        )
        url = get_remote_url(temp_dir, "origin")
        assert url == "git@github.com:owner/repo.git"


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

    @pytest.mark.skipif(
        sys.platform == "win32" or getattr(os, "geteuid", lambda: -1)() == 0,
        reason="POSIX permission semantics; root bypasses chmod",
    )
    def test_git_config_permission_denied_raises(self, temp_dir: str) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.chmod(0o000)
        try:
            with pytest.raises(NotGitRepoError, match="Cannot read git config"):
                get_remote_url(temp_dir, "origin")
        finally:
            config.chmod(0o644)

    def test_git_config_invalid_utf8_raises(self, temp_dir: str) -> None:
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        config = Path(temp_dir) / ".git" / "config"
        config.write_bytes(b"[core]\n\tx = \xff\xfe\xfd\n")
        with pytest.raises(NotGitRepoError, match="invalid UTF-8"):
            get_remote_url(temp_dir, "origin")

    def test_get_remote_url_duplicate_keys(self, temp_git_repo_duplicate_keys: str) -> None:
        """Git configs with duplicate keys (e.g. VS Code's vscode-merge-base) should not crash."""
        url = get_remote_url(temp_git_repo_duplicate_keys, "origin")
        assert url == "git@github.com:testuser/testrepo.git"


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
        import logging

        caplog.set_level(logging.WARNING)
        # pyproject.toml without [project].name
        Path(temp_dir, "pyproject.toml").write_text("[project]\nversion = '1.0'\n")
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

    def test_invalid_toml_pyproject_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "pyproject.toml").write_text("this is not [valid toml !!!")
        with pytest.raises(ProjectMetadataError, match="Invalid pyproject.toml"):
            get_package_name(temp_dir, "pypi")

    def test_empty_pyproject_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "pyproject.toml").write_text("")
        with pytest.raises(ProjectMetadataError, match="No 'project.name'"):
            get_package_name(temp_dir, "pypi")

    def test_empty_package_json_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "package.json").write_text("")
        with pytest.raises(ProjectMetadataError, match="Invalid package.json"):
            get_package_name(temp_dir, "npm")

    def test_empty_cargo_toml_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "Cargo.toml").write_text("")
        with pytest.raises(ProjectMetadataError, match="No 'package.name'"):
            get_package_name(temp_dir, "cargo")

    def test_empty_go_mod_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "go.mod").write_text("")
        with pytest.raises(ProjectMetadataError, match="No 'module' declaration"):
            get_package_name(temp_dir, "go")

    def test_empty_composer_json_raises(self, temp_dir: str) -> None:
        Path(temp_dir, "composer.json").write_text("")
        with pytest.raises(ProjectMetadataError, match="Invalid composer.json"):
            get_package_name(temp_dir, "packagist")

    @pytest.mark.skipif(
        sys.platform == "win32" or getattr(os, "geteuid", lambda: -1)() == 0,
        reason="POSIX permission semantics; root bypasses chmod",
    )
    def test_pyproject_permission_denied_raises(self, temp_dir: str) -> None:
        path = Path(temp_dir) / "pyproject.toml"
        path.write_text("[project]\nname = 'x'\n")
        path.chmod(0o000)
        try:
            with pytest.raises(ProjectMetadataError, match="Cannot read pyproject.toml"):
                get_package_name(temp_dir, "pypi")
        finally:
            path.chmod(0o644)

    def test_pyproject_invalid_utf8_raises(self, temp_dir: str) -> None:
        path = Path(temp_dir) / "pyproject.toml"
        path.write_bytes(b"\xff\xfe\xfd invalid utf-8 \xc3\x28")
        with pytest.raises(ProjectMetadataError, match="Invalid pyproject.toml"):
            get_package_name(temp_dir, "pypi")

    def test_symlinked_pyproject_resolves(self, temp_dir: str, tmp_path: Path) -> None:
        """Reading pyproject.toml via a symlinked project dir works."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "pyproject.toml").write_text(
            '[project]\nname = "linked-project"\n'
        )
        link_dir = Path(temp_dir) / "link"
        link_dir.symlink_to(real_dir, target_is_directory=True)
        assert get_package_name(str(link_dir), "pypi") == "linked-project"
