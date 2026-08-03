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
from typing import cast

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
    except (OSError, UnicodeDecodeError) as exc:
        # UnicodeDecodeError is not an OSError; catch it too so a pins file
        # with non-UTF-8 bytes is treated as corrupt instead of crashing the
        # TUI at startup (load_pins runs in OlinkTUI.__init__).
        logger.warning("Could not read pins file %s: %s", path, exc)
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Ignoring corrupt pins file %s: %s", path, exc)
        return []

    # json.loads returns Any; cast the validated shapes to concrete types so
    # strict type checkers see known types instead of "partially unknown".
    if not isinstance(data, dict):
        return []
    pins = cast("dict[str, object]", data).get("pins")
    if not isinstance(pins, list):
        return []
    return [name for name in cast("list[object]", pins) if isinstance(name, str)]


def save_pins(pins: list[str]) -> None:
    """Write the pin list, creating the config directory if needed.

    Writes to a sibling temp file and atomically renames it into place so a
    crash mid-write can never truncate ``pins.json`` (which ``load_pins`` would
    then silently read as an empty list, losing every pin).
    """
    path = pins_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(json.dumps({"pins": pins}, indent=2) + "\n", encoding="utf-8")
    Path(tmp).replace(path)
