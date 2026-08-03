# Pinned Targets (TUI) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let TUI users pin frequently-used targets so they float to the top of the list and persist globally across sessions.

**Architecture:** A new pure-stdlib persistence module (`core/pins.py`) reads/writes a JSON list of pinned target names under the XDG config dir. The TUI loads pins on startup, applies a pinned-first ordering to whichever source list is showing, marks pinned rows with `★`, and toggles pins with the `p` key (persisting on each toggle).

**Tech Stack:** Python 3.14+, Typer (CLI, untouched here), Textual (TUI), stdlib `json`/`os`/`pathlib`. pytest for tests. **No new runtime dependency.**

## Global Constraints

- Python 3.14+; type hints mandatory on all args and return values (PEP 8, ruff defaults).
- No new runtime dependency — pins use only stdlib (`json`, `os`, `pathlib`).
- Custom exceptions come from `olink.core.exceptions`; never raise generic `Exception`. (Persistence uses stdlib `OSError`/`json.JSONDecodeError`, caught internally — no new custom exception needed.)
- Pins are **global** (one list for the user, applied in every project).
- Storage: `$XDG_CONFIG_HOME/olink/pins.json`, falling back to `~/.config/olink/pins.json`. Format: `{"pins": ["origin", "pypi"]}` — an ordered list of catalog target names.
- The TUI must never crash on a missing/corrupt/unreadable pins file (treat as empty, log a warning).
- Docstrings document **why**, not **what**, on public functions.
- Feature-grouped layout; keep `core/pins.py` free of any TUI import (regenerable in isolation).
- Update `JOURNAL.md` chronologically at the end.

---

### Task 1: Pins persistence module (`core/pins.py`)

Pure stdlib persistence. No Textual/Typer imports. This is the foundation the TUI consumes.

**Files:**
- Create: `src/olink/core/pins.py`
- Test: `tests/core/test_pins.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces:
  - `config_dir() -> Path` — `$XDG_CONFIG_HOME/olink` or `~/.config/olink`.
  - `pins_file() -> Path` — `config_dir() / "pins.json"`.
  - `load_pins() -> list[str]` — ordered pin names; `[]` on missing/corrupt.
  - `save_pins(pins: list[str]) -> None` — writes `{"pins": [...]}`, creating dirs.
  - `toggle_pin(name: str) -> list[str]` — load, toggle `name` (append on add, remove on unpin), save, return the new list.

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_pins.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/core/test_pins.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'olink.core.pins'`.

- [ ] **Step 3: Write the implementation**

Create `src/olink/core/pins.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/core/test_pins.py -v`
Expected: PASS (all 8 tests).

- [ ] **Step 5: Commit**

```bash
git add src/olink/core/pins.py tests/core/test_pins.py
git commit -m "feat(core): add global pin persistence"
```

---

### Task 2: Pinned-first ordering in models (`tui/models.py`)

Adds a `pinned` flag to `TargetItem` and a pure ordering helper. Kept pure (no app/widget state) so it is trivially unit-testable.

**Files:**
- Modify: `src/olink/tui/models.py`
- Test: `tests/tui/test_tui.py` (add a new test class)

**Interfaces:**
- Consumes: `TargetItem` (existing dataclass).
- Produces:
  - `TargetItem.pinned: bool` field (default `False`).
  - `order_by_pins(items: list[TargetItem], pinned: list[str]) -> list[TargetItem]` — sets each item's `pinned` flag by membership, then returns a new list with pinned items first (ordered by their index in `pinned`) followed by the remaining items in their original order. Names in `pinned` that are absent from `items` are ignored (this is what makes `available` mode "respect the mode").

- [ ] **Step 1: Write the failing tests**

Add to `tests/tui/test_tui.py`:

```python
class TestOrderByPins:
    """Tests for order_by_pins pinned-first ordering."""

    def test_pins_float_to_top_in_pin_order(self) -> None:
        from olink.tui.models import order_by_pins

        items = _make_items()  # names: pypi, npm, origin, issues, pypistats
        ordered = order_by_pins(items, ["origin", "pypi"])
        assert [i.name for i in ordered[:2]] == ["origin", "pypi"]

    def test_pinned_flag_is_set(self) -> None:
        from olink.tui.models import order_by_pins

        items = _make_items()
        ordered = order_by_pins(items, ["origin"])
        by_name = {i.name: i.pinned for i in ordered}
        assert by_name["origin"] is True
        assert by_name["npm"] is False

    def test_rest_keeps_original_order(self) -> None:
        from olink.tui.models import order_by_pins

        items = _make_items()
        original_rest = [i.name for i in items if i.name != "origin"]
        ordered = order_by_pins(items, ["origin"])
        assert [i.name for i in ordered[1:]] == original_rest

    def test_absent_pins_are_ignored(self) -> None:
        from olink.tui.models import order_by_pins

        items = _make_items()  # no "crates" here
        ordered = order_by_pins(items, ["crates", "npm"])
        assert ordered[0].name == "npm"
        assert len(ordered) == len(items)

    def test_empty_pins_returns_same_names_unpinned(self) -> None:
        from olink.tui.models import order_by_pins

        items = _make_items()
        ordered = order_by_pins(items, [])
        assert [i.name for i in ordered] == [i.name for i in items]
        assert all(i.pinned is False for i in ordered)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/tui/test_tui.py::TestOrderByPins -v`
Expected: FAIL with `ImportError: cannot import name 'order_by_pins'`.

- [ ] **Step 3: Write the implementation**

In `src/olink/tui/models.py`, add `pinned` to the dataclass:

```python
@dataclass
class TargetItem:
    """A target entry for display in the TUI."""

    name: str
    description: str
    target_cls: type[Target]
    ecosystem: str | None = None
    pinned: bool = False

    def get_url(self, cwd: str) -> str:
        """Resolve the URL for this target."""
        if self.ecosystem and issubclass(self.target_cls, MultiEcosystemTarget):
            return self.target_cls(ecosystem=self.ecosystem).get_url(cwd)
        return self.target_cls().get_url(cwd)
```

Add the ordering helper at the end of the module:

```python
def order_by_pins(items: list[TargetItem], pinned: list[str]) -> list[TargetItem]:
    """Return items pinned-first, marking each item's `pinned` flag.

    Pinned items come first in the order they appear in `pinned`; the rest keep
    their incoming order. Pin names absent from `items` are ignored, so in the
    TUI's "available" mode a pin only surfaces when it applies to this project.
    """
    rank = {name: index for index, name in enumerate(pinned)}
    for item in items:
        item.pinned = item.name in rank
    pinned_items = sorted(
        (item for item in items if item.pinned),
        key=lambda item: rank[item.name],
    )
    rest = [item for item in items if not item.pinned]
    return [*pinned_items, *rest]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/tui/test_tui.py::TestOrderByPins -v`
Expected: PASS (all 5 tests).

- [ ] **Step 5: Commit**

```bash
git add src/olink/tui/models.py tests/tui/test_tui.py
git commit -m "feat(tui): add pinned flag and pinned-first ordering"
```

---

### Task 3: Wire pinning into the TUI (`tui/app.py`, `tui/widgets.py`)

Load pins on startup, order the source list, render the `★` marker, and add the `p` toggle key with persistence + selection retention.

**Files:**
- Modify: `src/olink/tui/app.py`
- Modify: `src/olink/tui/widgets.py`
- Test: `tests/tui/test_tui.py` (add a new async test class)

**Interfaces:**
- Consumes: `load_pins`, `toggle_pin` from `olink.core.pins`; `order_by_pins` from `olink.tui.models`; `TargetRow`, `TargetListWidget`, `StatusBar` from `olink.tui.widgets`.
- Produces: `OlinkTUI.pinned: list[str]`; `OlinkTUI.action_toggle_pin()`; `★` marker rendering in `TargetRow`.

- [ ] **Step 1: Render the marker in `widgets.py`**

In `src/olink/tui/widgets.py`, replace `TargetRow.compose`:

```python
    def compose(self) -> ComposeResult:
        label = Text()
        marker = "★ " if self.item.pinned else "  "
        label.append(marker, style="yellow")
        label.append(f"{self.item.name:20s}", style="cyan")
        label.append(f" {self.item.description}")
        yield Static(label)
```

(The 2-char marker replaces the original single leading space, preserving column alignment.)

- [ ] **Step 2: Wire `app.py`**

In `src/olink/tui/app.py`:

Update imports near the top:

```python
from olink.core.pins import load_pins, toggle_pin
from olink.tui.models import (
    FilterState,
    TargetItem,
    build_all_targets,
    build_available_targets,
    order_by_pins,
)
```

Update `HEADER_TEXT`:

```python
HEADER_TEXT = (
    "olink — Interactive Target Browser\n"
    "Tab: toggle view  j/k: navigate  /: search  o: open  c: copy  p: pin  q: quit"
)
```

Add the binding to `BINDINGS` (after the `c` binding):

```python
        Binding("p", "toggle_pin", "Pin"),
```

In `__init__`, load pins (after `self.searching = False`):

```python
        self.pinned = load_pins()
```

Change `_source` to apply pin ordering:

```python
    def _source(self) -> list[TargetItem]:
        base = self.available_targets if self.state.mode == "available" else self.all_targets
        return order_by_pins(base, self.pinned)
```

Add the toggle action and a selection helper (near the other actions, e.g. after `action_copy_target`):

```python
    def action_toggle_pin(self) -> None:
        """Pin/unpin the highlighted target, persist, and keep it selected."""
        target_list = self.query_one(TargetListWidget)
        item = target_list.get_selected_item()
        if item is None:
            return
        name = item.name
        status = self.query_one(StatusBar)
        try:
            self.pinned = toggle_pin(name)
        except OSError as exc:
            # Persisting failed; still toggle in memory so the session works.
            if name in self.pinned:
                self.pinned = [existing for existing in self.pinned if existing != name]
            else:
                self.pinned = [*self.pinned, name]
            status.set_error(f"Could not save pins: {exc}")
        self._refresh_list()
        self._reselect(name)

    def _reselect(self, name: str) -> None:
        """Move the cursor back onto the row for `name` after a refresh."""
        target_list = self.query_one(TargetListWidget)
        for index, row in enumerate(target_list.query(TargetRow)):
            if row.item.name == name:
                target_list.index = index
                return
```

Add `TargetRow` to the widgets import at the top of `app.py`:

```python
from olink.tui.widgets import SearchInput, StatusBar, TargetListWidget, TargetRow
```

- [ ] **Step 3: Write the failing tests**

Add to `tests/tui/test_tui.py`:

```python
class TestPinningInTUI:
    """Tests for pin loading, ordering, marker, and the p toggle."""

    def _app(self, pinned: list[str]) -> OlinkTUI:
        items = _make_items()
        with (
            patch("olink.tui.app.build_all_targets", return_value=items),
            patch("olink.tui.app.build_available_targets", return_value=items),
            patch("olink.tui.app.load_pins", return_value=pinned),
        ):
            return OlinkTUI(cwd="/tmp")

    @pytest.mark.asyncio
    async def test_pinned_target_renders_first(self) -> None:
        app = self._app(["origin"])
        async with app.run_test() as pilot:
            await pilot.pause()
            rows = list(app.query_one(TargetListWidget).query(TargetRow))
            assert rows[0].item.name == "origin"
            assert rows[0].item.pinned is True

    @pytest.mark.asyncio
    async def test_p_key_pins_selected_and_persists(self) -> None:
        app = self._app([])
        with patch("olink.tui.app.toggle_pin", return_value=["pypi"]) as toggle:
            async with app.run_test() as pilot:
                await pilot.pause()
                target_list = app.query_one(TargetListWidget)
                target_list.index = 0  # "pypi" is first in _make_items()
                await pilot.pause()
                selected = target_list.get_selected_item()
                assert selected is not None
                await pilot.press("p")
                await pilot.pause()
                toggle.assert_called_once_with(selected.name)
                assert app.pinned == ["pypi"]

    @pytest.mark.asyncio
    async def test_p_key_keeps_selection_on_same_target(self) -> None:
        app = self._app([])
        with patch("olink.tui.app.toggle_pin", return_value=["issues"]):
            async with app.run_test() as pilot:
                await pilot.pause()
                target_list = app.query_one(TargetListWidget)
                # Select "issues" (not first), then pin it.
                names = [r.item.name for r in target_list.query(TargetRow)]
                target_list.index = names.index("issues")
                await pilot.pause()
                await pilot.press("p")
                await pilot.pause()
                assert target_list.get_selected_item().name == "issues"

    @pytest.mark.asyncio
    async def test_save_failure_shows_error_but_toggles_memory(self) -> None:
        app = self._app([])
        with patch("olink.tui.app.toggle_pin", side_effect=OSError("read-only")):
            async with app.run_test() as pilot:
                await pilot.pause()
                target_list = app.query_one(TargetListWidget)
                target_list.index = 0
                await pilot.pause()
                name = target_list.get_selected_item().name
                await pilot.press("p")
                await pilot.pause()
                assert name in app.pinned
                status = _status_text(app.query_one(StatusBar))
                assert "Could not save pins" in status
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `uv run pytest tests/tui/test_tui.py::TestPinningInTUI -v`
Expected: PASS (all 4 tests). If any fail, fix `app.py`/`widgets.py` before continuing.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q`
Expected: PASS (all tests, including pre-existing ones — confirms the marker change didn't break `TestTargetListRendering`).

- [ ] **Step 6: Commit**

```bash
git add src/olink/tui/app.py src/olink/tui/widgets.py tests/tui/test_tui.py
git commit -m "feat(tui): pin targets with p key, float pinned to top"
```

---

### Task 4: Docs & journal

**Files:**
- Modify: `README.md`
- Modify: `JOURNAL.md`

- [ ] **Step 1: Document the feature in `README.md`**

Find the TUI section (search for the key hints like `Tab:` / `search` / `open`). Add pinning to the documented keybindings and a short paragraph:

```markdown
- `p` — pin/unpin the highlighted target. Pinned targets are marked with `★`
  and float to the top of the list in every project. Pins are stored in
  `$XDG_CONFIG_HOME/olink/pins.json` (default `~/.config/olink/pins.json`).
```

- [ ] **Step 2: Append a `JOURNAL.md` entry**

Add a dated entry (2026-08-03) summarizing: added global pin persistence (`core/pins.py`, stdlib JSON under XDG), pinned-first ordering in the TUI, `p` toggle key, `★` marker; decision to keep pins global and TUI-only per the design spec; write failures degrade gracefully (error in status bar, in-memory toggle still applies).

- [ ] **Step 3: Commit**

```bash
git add README.md JOURNAL.md
git commit -m "docs: document TUI pinning"
```

---

## Self-Review

**1. Spec coverage** (against `docs/superpowers/specs/2026-08-03-pinned-targets-tui-design.md`):
- `p` toggle → Task 3 binding + `action_toggle_pin`. ✓
- Float to top, `★`, pin-order, rest alphabetical → Task 2 `order_by_pins` (rest keeps incoming order, which `build_*` already sorts alphabetically) + Task 3 marker. ✓
- Both modes; `available` respects availability → `order_by_pins` ignores absent pins; `_source` applies it to whichever base list. ✓
- Search keeps pins on top → ordering applied in `_source`, which `_filter_items` reads from; filtering preserves order. ✓ (Covered by design; no separate test added — `_filter_items` already tested, order preservation is inherent to the list comprehension.)
- Storage location/format, stdlib, no dep → Task 1. ✓
- Missing→[], corrupt→[]+warn, unknown names ignored, write failure surfaced → Task 1 (`load_pins`) + Task 3 (`action_toggle_pin` OSError path). ✓
- Code shape (`core/pins.py`, `models.py`, `app.py`, `widgets.py`, header) → Tasks 1–3. ✓
- Tests enumerated in spec → Tasks 1–3 map 1:1. ✓
- Out-of-scope items → none implemented. ✓

**2. Placeholder scan:** No TBD/TODO; all code steps contain full code; README/journal steps specify exact content to add. ✓

**3. Type consistency:** `load_pins`/`toggle_pin`/`save_pins`/`config_dir`/`pins_file` names identical across Task 1 def and Task 3 use. `order_by_pins(items, pinned)` signature identical across Task 2 def and Task 3 use. `TargetItem.pinned` set in Task 2, read in Task 3 `widgets.py`. `_reselect`/`action_toggle_pin` self-consistent. ✓

**Note on spec deviation:** The spec listed `toggle_pin` as an app-side helper; here it lives in `core/pins.py` (pure persistence) and the app calls it, with an in-memory fallback on write failure. This keeps `core/pins.py` as the single persistence unit and the app free of file I/O logic — a refinement, fully preserving spec behavior.
