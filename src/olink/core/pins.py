"""Global pin persistence.

Pins are the first user-global state olink stores (everything else is derived
from project files). Kept as a plain ordered JSON list so it can be edited by
hand and rewritten from scratch. Failures here must never break the TUI, so
read errors degrade to an empty list rather than raising.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def config_dir() -> Path:
    """Resolve olink's config directory, honoring XDG_CONFIG_HOME."""
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / "olink"


def pins_file() -> Path:
    """Path to the JSON file holding the ordered list of pinned target names."""
    return config_dir() / "pins.json"


def load_pins() -> list[str]:
    """Return pinned target names in order; empty on missing/corrupt/unreadable."""
    path = pins_file()
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as exc:
        logger.warning("Could not read pins file %s: %s", path, exc)
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Ignoring corrupt pins file %s: %s", path, exc)
        return []

    pins = data.get("pins") if isinstance(data, dict) else None
    if not isinstance(pins, list):
        return []
    return [name for name in pins if isinstance(name, str)]


def save_pins(pins: list[str]) -> None:
    """Write the pin list, creating the config directory if needed."""
    path = pins_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pins": pins}, indent=2) + "\n", encoding="utf-8")


def toggle_pin(name: str) -> list[str]:
    """Toggle a target's pinned state and persist. Returns the new pin list.

    Newly pinned names are appended so the pinned group stays in the order the
    user pinned things.
    """
    pins = load_pins()
    if name in pins:
        pins = [existing for existing in pins if existing != name]
    else:
        pins = [*pins, name]
    save_pins(pins)
    return pins
