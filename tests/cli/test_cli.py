"""Tests for CLI interface."""

import subprocess
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from olink.cli.app import app

runner = CliRunner()


class TestCLIHelp:
    """Tests for CLI help and basic commands."""

    def test_help_shows_usage(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Open external URLs" in result.stdout

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
        assert "pypi.org/project/test-project" in result.stdout


    def test_dry_run_piwheels(self, temp_pyproject: str) -> None:
        """Verify dry-run output includes piwheels so users can trust non-opening previews."""
        result = runner.invoke(app, ["-n", "-d", temp_pyproject, "piwheels"])
        assert result.exit_code == 0
        assert "piwheels.org/project/test-project" in result.stdout

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
        with open(filepath, "w") as f:
            f.write("hello")
        result = runner.invoke(app, ["-d", filepath, "origin"])
        assert result.exit_code == 1
        assert "Not a directory" in result.output

    def test_list_no_targets_available(self, temp_dir: str) -> None:
        result = runner.invoke(app, ["--list", "-d", temp_dir])
        assert result.exit_code == 0
        assert "No targets available for this project." in result.stdout


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
