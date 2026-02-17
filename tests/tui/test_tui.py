"""Tests for TUI actions, models, and widgets."""

from unittest.mock import patch

import pyperclip
import pytest

from olink.core.targets import Target
from olink.tui.actions import copy_to_clipboard
from olink.tui.app import OlinkTUI
from olink.tui.models import TargetItem, build_all_targets, build_available_targets


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


class _DummyTarget(Target):
    """Minimal Target subclass for testing."""

    name = "dummy"
    description = "dummy"

    def get_url(self, cwd: str) -> str:
        return "https://example.com"


def _item(name: str, description: str) -> TargetItem:
    return TargetItem(
        name=name, description=description, target_cls=_DummyTarget
    )


def _make_items() -> list[TargetItem]:
    """Create a fixed set of TargetItems for filter tests."""
    return [
        _item("pypi", "Open the PyPI page"),
        _item("npm", "Open the npm page"),
        _item("origin", "Open the remote origin URL"),
        _item("issues", "Open the issues page"),
        _item("pypistats", "Open the PyPI Stats page"),
    ]


class TestSearchFiltering:
    """Tests for the _filter_items search logic."""

    @pytest.fixture()
    def tui(self) -> OlinkTUI:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        return app

    def test_empty_query_returns_all(self, tui: OlinkTUI) -> None:
        result = tui._filter_items("")
        assert len(result) == 5

    def test_filter_by_name(self, tui: OlinkTUI) -> None:
        result = tui._filter_items("pypi")
        names = {item.name for item in result}
        assert "pypi" in names
        assert "pypistats" in names
        assert "npm" not in names

    def test_filter_by_description(self, tui: OlinkTUI) -> None:
        result = tui._filter_items("remote")
        assert len(result) == 1
        assert result[0].name == "origin"

    def test_filter_case_insensitive(self, tui: OlinkTUI) -> None:
        result_lower = tui._filter_items("pypi")
        result_upper = tui._filter_items("PYPI")
        result_mixed = tui._filter_items("PyPi")
        assert len(result_lower) == len(result_upper) == len(result_mixed)

    def test_filter_no_matches(self, tui: OlinkTUI) -> None:
        result = tui._filter_items("zzzzzzz")
        assert result == []

    def test_filter_matches_description_keyword(self, tui: OlinkTUI) -> None:
        result = tui._filter_items("Stats")
        assert len(result) == 1
        assert result[0].name == "pypistats"
