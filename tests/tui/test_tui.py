"""Tests for TUI actions, models, and widgets."""

from unittest.mock import patch

import pyperclip
import pytest

from olink.tui.actions import copy_to_clipboard
from olink.tui.models import build_all_targets, build_available_targets


class TestCopyToClipboard:
    """Tests for copy_to_clipboard action."""

    def test_copy_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pyperclip, "copy", lambda text: None)
        assert copy_to_clipboard("https://example.com") is True

    def test_copy_failure_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def failing_copy(text: str) -> None:
            raise pyperclip.PyperclipException("no clipboard")

        monkeypatch.setattr(pyperclip, "copy", failing_copy)
        assert copy_to_clipboard("https://example.com") is False


class TestBuildTargets:
    """Tests for target list building."""

    def test_build_all_targets_returns_all_registered(self) -> None:
        from olink.core.catalog import REGISTRY

        items = build_all_targets()
        assert len(items) == len(REGISTRY)
        names = {item.name for item in items}
        assert "origin" in names
        assert "pypi" in names

    def test_build_available_targets_pyproject(self, temp_pyproject: str) -> None:
        items = build_available_targets(temp_pyproject)
        names = {item.name for item in items}
        assert "pypi" in names
        assert "origin" not in names

    def test_build_available_targets_git_repo(self, temp_git_repo: str) -> None:
        items = build_available_targets(temp_git_repo)
        names = {item.name for item in items}
        assert "origin" in names
        assert "issues" in names

    def test_build_available_targets_empty_dir(self, temp_dir: str) -> None:
        items = build_available_targets(temp_dir)
        assert items == []

    def test_build_available_multi_ecosystem_expanded(self, temp_multi_ecosystem: str) -> None:
        items = build_available_targets(temp_multi_ecosystem)
        names = {item.name for item in items}
        # Multi-ecosystem targets should be expanded with ecosystem suffixes
        has_suffix = any(":" in name for name in names)
        assert has_suffix
