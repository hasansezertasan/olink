"""Tests for CLI interface."""

import pathlib
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from olink.cli.app import app

if TYPE_CHECKING:
    import pytest

runner = CliRunner()


class TestCLIHelp:
    """Tests for CLI help and basic commands."""

    def test_help_shows_usage(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Open external URLs" in result.stdout

    def test_version_flag(self) -> None:
        """`--version` must print `olink <version>` and exit 0 without a target."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.stdout.startswith("olink ")

    def test_version_short_flag(self) -> None:
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert result.stdout.startswith("olink ")

    def test_version_renders_package_version(self, monkeypatch) -> None:
        """`--version` must echo exactly the `__version__` it imported.

        `__version__` now comes from the git tag via hatch-vcs (generated
        `olink/_version.py`), so this pins the wiring, not a literal: monkeypatch the
        symbol the CLI module imported and assert the flag prints it verbatim.
        """
        import sys

        cli_module = sys.modules["olink.cli.app"]
        monkeypatch.setattr(cli_module, "__version__", "9.9.9")
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "olink 9.9.9"

    def test_list_all_targets(self) -> None:
        result = runner.invoke(app, ["--list-all"])
        assert result.exit_code == 0
        assert "origin" in result.stdout
        assert "pypi" in result.stdout
        assert "issues" in result.stdout

    def test_list_shows_only_working_targets(self, temp_pyproject: str) -> None:
        result = runner.invoke(app, ["--list", "-d", temp_pyproject])
        assert result.exit_code == 0
        assert "pypi" in result.stdout
        assert "pepy" in result.stdout
        assert "piwheels" in result.stdout
        assert "bundlephobia" not in result.stdout
        assert "targets available)" in result.stdout

    def test_list_with_git_repo(self, temp_git_repo: str) -> None:
        result = runner.invoke(app, ["--list", "-d", temp_git_repo])
        assert result.exit_code == 0
        assert "origin" in result.stdout
        assert "issues" in result.stdout


class TestCLIDryRun:
    """Tests for CLI dry-run mode."""

    def test_dry_run_pypi(self, temp_pyproject: str) -> None:
        result = runner.invoke(app, ["-n", "-d", temp_pyproject, "pypi"])
        assert result.exit_code == 0
        assert "https://pypi.org/project/test-project/" in result.stdout

    def test_dry_run_piwheels(self, temp_pyproject: str) -> None:
        """Ensure dry-run mode reveals the exact piwheels URL before opening a browser."""
        result = runner.invoke(app, ["-n", "-d", temp_pyproject, "piwheels"])
        assert result.exit_code == 0
        assert "https://www.piwheels.org/project/test-project/" in result.stdout

    def test_dry_run_npm(self, temp_package_json: str) -> None:
        result = runner.invoke(app, ["-n", "-d", temp_package_json, "npm"])
        assert result.exit_code == 0
        assert "npmjs.com/package/test-project" in result.stdout

    def test_dry_run_origin(self, temp_git_repo: str) -> None:
        result = runner.invoke(app, ["-n", "-d", temp_git_repo, "origin"])
        assert result.exit_code == 0
        assert "github.com/testuser/testrepo" in result.stdout

    def test_dry_run_issues(self, temp_git_repo: str) -> None:
        result = runner.invoke(app, ["-n", "-d", temp_git_repo, "issues"])
        assert result.exit_code == 0
        assert "github.com/testuser/testrepo/issues" in result.stdout

    def test_piwheels_without_pyproject(self, temp_dir: str) -> None:
        """Verify CLI errors stay actionable when piwheels is run outside Python projects."""
        result = runner.invoke(app, ["-n", "-d", temp_dir, "piwheels"])
        assert result.exit_code == 1
        assert "No pyproject.toml found" in result.output


class TestCLIErrors:
    """Tests for CLI error handling."""

    def test_unknown_target(self) -> None:
        result = runner.invoke(app, ["nonexistent"])
        assert result.exit_code == 1
        assert "Unknown target" in result.output

    def test_no_origin_remote(self, temp_dir: str) -> None:
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        result = runner.invoke(app, ["-d", temp_dir, "origin"])
        assert result.exit_code == 1
        assert "No 'origin' remote configured" in result.output

    def test_not_git_repo(self, temp_dir: str) -> None:
        result = runner.invoke(app, ["-d", temp_dir, "origin"])
        assert result.exit_code == 1
        assert "not inside a git repository" in result.output

    def test_nonexistent_directory(self) -> None:
        result = runner.invoke(app, ["-d", "/nonexistent/path", "origin"])
        assert result.exit_code == 1
        assert "Directory does not exist" in result.output

    def test_directory_is_file(self, temp_dir: str) -> None:
        import os

        filepath = os.path.join(temp_dir, "afile.txt")
        pathlib.Path(filepath).write_text("hello", encoding="utf-8")
        result = runner.invoke(app, ["-d", filepath, "origin"])
        assert result.exit_code == 1
        assert "Not a directory" in result.output

    def test_list_no_targets_available(self, temp_dir: str) -> None:
        result = runner.invoke(app, ["--list", "-d", temp_dir])
        assert result.exit_code == 0
        assert "No targets available for this project." in result.stdout

    def test_list_excludes_codecov_on_gitea(self, temp_git_repo_gitea: str) -> None:
        """Codecov target must NOT show in `--list` for self-hosted gitea repos.

        Earlier silent-bad-URL behavior would have erroneously listed it.
        """
        result = runner.invoke(app, ["--list", "-d", temp_git_repo_gitea])
        assert result.exit_code == 0
        assert "codecov" not in result.stdout
        assert "coveralls" not in result.stdout
        assert "origin" in result.stdout

    def test_list_excludes_codecov_on_forgejo(self, temp_git_repo_forgejo: str) -> None:
        """Mirror of the gitea exclusion test for forgejo. Guards platform-detection drift."""
        result = runner.invoke(app, ["--list", "-d", temp_git_repo_forgejo])
        assert result.exit_code == 0
        assert "codecov" not in result.stdout
        assert "coveralls" not in result.stdout
        assert "origin" in result.stdout

    def test_list_excludes_codecov_on_codeberg(self, temp_git_repo_codeberg: str) -> None:
        """Codeberg resolves to forgejo platform and must inherit the same exclusion."""
        result = runner.invoke(app, ["--list", "-d", temp_git_repo_codeberg])
        assert result.exit_code == 0
        assert "codecov" not in result.stdout
        assert "coveralls" not in result.stdout
        assert "origin" in result.stdout

    def test_subdir_does_not_resolve_parent_pyproject(self, temp_pyproject: str) -> None:
        """README documents: olink must be run from project root.

        From `src/` (no pyproject.toml there), `olink pypi` must error rather
        than silently traverse upward.
        """
        import os

        subdir = os.path.join(temp_pyproject, "src")
        pathlib.Path(subdir).mkdir(parents=True)
        result = runner.invoke(app, ["-n", "-d", subdir, "pypi"])
        assert result.exit_code == 1
        assert "No pyproject.toml found" in result.output


class TestCLIOpenBrowser:
    """Tests for CLI browser opening (mocked)."""

    @patch("typer.launch")
    def test_opens_browser(self, mock_launch: MagicMock, temp_pyproject: str) -> None:
        result = runner.invoke(app, ["-d", temp_pyproject, "pypi"])
        assert result.exit_code == 0
        assert "Opening:" in result.stdout
        mock_launch.assert_called_once()

    @patch("typer.launch")
    def test_opens_correct_url(self, mock_launch: MagicMock, temp_git_repo: str) -> None:
        runner.invoke(app, ["-d", temp_git_repo, "origin"])
        mock_launch.assert_called_with("https://github.com/testuser/testrepo")


class TestCLITUILaunch:
    """Tests for TUI launch path."""

    @patch("olink.tui.launch_tui")
    def test_no_target_launches_tui(self, mock_tui: MagicMock, temp_dir: str) -> None:
        result = runner.invoke(app, ["-d", temp_dir])
        assert result.exit_code == 0
        mock_tui.assert_called_once()

    @patch("olink.tui.launch_tui", side_effect=KeyboardInterrupt)
    def test_tui_keyboard_interrupt_handled(self, mock_tui: MagicMock, temp_dir: str) -> None:
        result = runner.invoke(app, ["-d", temp_dir])
        assert result.exit_code == 0

    def test_tui_missing_optional_deps_shows_hint(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: str
    ) -> None:
        """When a TUI optional dep is missing, the CLI prints an install hint and exits 1."""
        import builtins

        real_import = builtins.__import__

        def fake_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "olink.tui":
                msg = "No module named 'textual'"
                raise ImportError(msg, name="textual")
            return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(builtins, "__import__", fake_import)
        result = runner.invoke(app, ["-d", temp_dir])
        assert result.exit_code == 1
        assert "requires extra dependencies" in result.output

    def test_tui_unrelated_import_error_propagates(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: str
    ) -> None:
        """An ImportError unrelated to the TUI optional deps must not be swallowed."""
        import builtins

        real_import = builtins.__import__

        def fake_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "olink.tui":
                msg = "boom"
                raise ImportError(msg, name="some_unrelated_module")
            return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(builtins, "__import__", fake_import)
        result = runner.invoke(app, ["-d", temp_dir])
        assert isinstance(result.exception, ImportError)


class TestCLIEntryPoint:
    """Tests for the module entry point."""

    def test_main_invokes_app(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys

        app_module = sys.modules["olink.cli.app"]
        called: list[bool] = []
        monkeypatch.setattr(app_module, "app", lambda: called.append(True))
        app_module.main()
        assert called == [True]
