"""Tests for global pin persistence."""

import json
from pathlib import Path

import pytest

from olink.core.pins import (
    config_dir,
    load_pins,
    pins_file,
    save_pins,
    toggle_pin,
)


@pytest.fixture()
def xdg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the config dir at a temp location via XDG_CONFIG_HOME."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


def test_config_dir_honors_xdg(xdg: Path) -> None:
    assert config_dir() == xdg / "olink"
    assert pins_file() == xdg / "olink" / "pins.json"


def test_config_dir_falls_back_to_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/x")))
    assert config_dir() == Path("/home/x/.config/olink")


def test_load_missing_returns_empty(xdg: Path) -> None:
    assert load_pins() == []


def test_save_then_load_round_trips_order(xdg: Path) -> None:
    save_pins(["origin", "pypi"])
    assert load_pins() == ["origin", "pypi"]


def test_save_creates_config_dir(xdg: Path) -> None:
    assert not (xdg / "olink").exists()
    save_pins(["origin"])
    assert pins_file().exists()


def test_load_corrupt_returns_empty(xdg: Path) -> None:
    pins_file().parent.mkdir(parents=True)
    pins_file().write_text("{not json", encoding="utf-8")
    assert load_pins() == []


def test_load_ignores_non_string_and_wrong_shape(xdg: Path) -> None:
    pins_file().parent.mkdir(parents=True)
    pins_file().write_text(json.dumps({"pins": ["origin", 5, None]}), encoding="utf-8")
    assert load_pins() == ["origin"]
    pins_file().write_text(json.dumps(["origin"]), encoding="utf-8")
    assert load_pins() == []


def test_toggle_adds_then_removes(xdg: Path) -> None:
    assert toggle_pin("origin") == ["origin"]
    assert toggle_pin("pypi") == ["origin", "pypi"]
    assert toggle_pin("origin") == ["pypi"]
    assert load_pins() == ["pypi"]
