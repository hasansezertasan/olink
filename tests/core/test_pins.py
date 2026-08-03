"""Tests for global pin persistence."""

import json
from pathlib import Path

import pytest

from olink.core.pins import (
    config_dir,
    load_pins,
    pins_file,
    save_pins,
)


@pytest.fixture()
def xdg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the config dir at a temp location via XDG_CONFIG_HOME."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


class TestPinsPersistence:
    """Tests for the config-dir resolution and load/save round-tripping."""

    def test_config_dir_honors_xdg(self, xdg: Path) -> None:
        assert config_dir() == xdg / "olink"
        assert pins_file() == xdg / "olink" / "pins.json"

    def test_config_dir_falls_back_to_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/x")))
        assert config_dir() == Path("/home/x/.config/olink")

    def test_load_missing_returns_empty(self, xdg: Path) -> None:
        assert load_pins() == []

    def test_save_then_load_round_trips_order(self, xdg: Path) -> None:
        save_pins(["origin", "pypi"])
        assert load_pins() == ["origin", "pypi"]

    def test_save_creates_config_dir(self, xdg: Path) -> None:
        assert not (xdg / "olink").exists()
        save_pins(["origin"])
        assert pins_file().exists()

    def test_load_corrupt_returns_empty(self, xdg: Path) -> None:
        pins_file().parent.mkdir(parents=True)
        pins_file().write_text("{not json", encoding="utf-8")
        assert load_pins() == []

    def test_load_invalid_utf8_returns_empty(self, xdg: Path) -> None:
        # Non-UTF-8 bytes raise UnicodeDecodeError (not OSError); load_pins must
        # still degrade to [] so the TUI does not crash at startup.
        pins_file().parent.mkdir(parents=True)
        pins_file().write_bytes(b"\xff\xfe not utf-8")
        assert load_pins() == []

    def test_load_ignores_non_string_and_wrong_shape(self, xdg: Path) -> None:
        pins_file().parent.mkdir(parents=True)
        pins_file().write_text(json.dumps({"pins": ["origin", 5, None]}), encoding="utf-8")
        assert load_pins() == ["origin"]
        pins_file().write_text(json.dumps(["origin"]), encoding="utf-8")
        assert load_pins() == []

    def test_save_overwrites_and_leaves_no_temp_file(self, xdg: Path) -> None:
        save_pins(["origin"])
        save_pins(["pypi"])
        assert load_pins() == ["pypi"]
        # Atomic write renames the temp file into place — nothing should linger.
        assert list((xdg / "olink").glob("*.tmp")) == []
