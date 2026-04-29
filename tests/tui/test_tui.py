"""Tests for TUI actions, models, and widgets."""

from unittest.mock import patch

import pyperclip
import pytest

from olink.core.targets import Target
from olink.tui.actions import copy_to_clipboard, open_in_browser
from olink.tui.app import OlinkTUI
from olink.tui.models import TargetItem, build_all_targets, build_available_targets
from olink.tui.widgets import SearchInput, StatusBar, TargetListWidget, TargetRow


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
    return TargetItem(name=name, description=description, target_cls=_DummyTarget)


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


def _status_text(status: StatusBar) -> str:
    """Render the StatusBar's content to a plain string for assertions."""
    rendered = status.render()
    plain = getattr(rendered, "plain", None)
    return plain if isinstance(plain, str) else str(rendered)


class TestOpenInBrowser:
    """Tests for open_in_browser action."""

    def test_open_in_browser_invokes_webbrowser(self, monkeypatch: pytest.MonkeyPatch) -> None:
        called = {}

        def fake_open(url: str) -> bool:
            called["url"] = url
            return True

        monkeypatch.setattr("olink.tui.actions.webbrowser.open", fake_open)
        result = open_in_browser("https://example.com")
        assert result is True
        assert called["url"] == "https://example.com"


class TestStatusBarRendering:
    """Tests for StatusBar message formatting and color state."""

    @pytest.mark.asyncio
    async def test_status_update_shows_mode_and_count(self) -> None:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            status = app.query_one(StatusBar)
            text = _status_text(status)
            assert "Available" in text
            assert "5/5" in text

    @pytest.mark.asyncio
    async def test_set_error_changes_color(self) -> None:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            status = app.query_one(StatusBar)
            status.set_error("boom")
            assert "boom" in _status_text(status)
            color = status.styles.color
            assert color is not None
            # "Red-like": red channel dominates green and blue. Avoids
            # coupling the test to a specific theme RGB.
            assert color.r > color.g and color.r > color.b


class TestTargetListRendering:
    """Tests for TargetListWidget rendering and selection."""

    @pytest.mark.asyncio
    async def test_list_renders_all_items(self) -> None:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            target_list = app.query_one(TargetListWidget)
            rows = list(target_list.query(TargetRow))
            assert len(rows) == 5
            assert {r.item.name for r in rows} == {"pypi", "npm", "origin", "issues", "pypistats"}

    @pytest.mark.asyncio
    async def test_get_selected_item_returns_highlighted(self) -> None:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            target_list = app.query_one(TargetListWidget)
            target_list.index = 0
            await pilot.pause()
            selected = target_list.get_selected_item()
            assert selected is not None
            assert selected.name == "pypi"


class TestActionHandlers:
    """Tests for action_open_target / action_copy_target via Pilot."""

    @pytest.mark.asyncio
    async def test_action_open_target_calls_open_in_browser(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        items = _make_items()
        opened: list[str] = []
        monkeypatch.setattr("olink.tui.app.open_in_browser", lambda url: opened.append(url) or True)
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            target_list = app.query_one(TargetListWidget)
            target_list.index = 0
            await pilot.pause()
            app.action_open_target()
            await pilot.pause()
            assert opened == ["https://example.com"]
            status_text = _status_text(app.query_one(StatusBar))
            assert "Opened" in status_text

    @pytest.mark.asyncio
    async def test_action_copy_target_uses_clipboard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        items = _make_items()
        copied: list[str] = []
        monkeypatch.setattr(
            "olink.tui.app.copy_to_clipboard",
            lambda url: copied.append(url) or True,
        )
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            target_list = app.query_one(TargetListWidget)
            target_list.index = 0
            await pilot.pause()
            app.action_copy_target()
            await pilot.pause()
            assert copied == ["https://example.com"]
            assert "Copied" in _status_text(app.query_one(StatusBar))

    @pytest.mark.asyncio
    async def test_action_copy_failure_sets_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        items = _make_items()
        monkeypatch.setattr("olink.tui.app.copy_to_clipboard", lambda url: False)
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            target_list = app.query_one(TargetListWidget)
            target_list.index = 0
            await pilot.pause()
            app.action_copy_target()
            await pilot.pause()
            text = _status_text(app.query_one(StatusBar))
            assert "Clipboard not available" in text

    @pytest.mark.asyncio
    async def test_toggle_mode_switches_view(self) -> None:
        items_avail = [_item("npm", "npm only")]
        items_all = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items_all),
            patch("olink.tui.app.build_available_targets", return_value=items_avail),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.state.mode == "available"
            app.action_toggle_mode()
            await pilot.pause()
            assert app.state.mode == "all"
            rows = list(app.query_one(TargetListWidget).query(TargetRow))
            assert len(rows) == 5

    @pytest.mark.asyncio
    async def test_search_flow_filters_then_cancels(self) -> None:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
        ):
            app = OlinkTUI(cwd="/tmp")
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_start_search()
            await pilot.pause()
            search = app.query_one(SearchInput)
            assert search.display is True
            search.value = "pypi"
            await pilot.pause()
            rows = list(app.query_one(TargetListWidget).query(TargetRow))
            assert {r.item.name for r in rows} == {"pypi", "pypistats"}
            app.action_cancel_search()
            await pilot.pause()
            assert search.display is False
            assert app.searching is False
