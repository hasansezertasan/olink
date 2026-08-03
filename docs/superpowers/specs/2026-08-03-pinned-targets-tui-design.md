# Design: Pinned targets (TUI)

**Status:** Approved
**Date:** 2026-08-03
**Scope:** TUI only

## Problem

Users who repeatedly open the same targets (e.g. `origin` and `pypi`) must
scroll past a long, alphabetically-sorted list in the TUI to reach them every
time. There is no way to prioritize frequently-used targets.

## Solution

Let users pin targets in the TUI. Pinned targets float to the top of the list
so they are always immediately reachable. Pins are global (shared across every
project) and persist between sessions.

This introduces the **first persistent user-global state** in olink. Until now
all state is derived from project files (git config, `pyproject.toml`, etc.).

## Behavior

- Press `p` on any target in the TUI to pin/unpin it.
- Pinned targets float to the **top** of the list (no separate section header),
  each marked with a `★`. Pin order = the order the user pinned them; everything
  below stays alphabetical.
- Works in both `available` and `all` modes. In `available` mode, pins only
  float up **among targets that are actually available** for the current repo —
  a `pypi` pin stays hidden in a Rust repo. This guarantees that opening a
  visible pin never produces a wrong-repo URL error.
- Search still works. Because pin-ordering is applied at the source list,
  pinned matches remain on top of filtered results too.

## Storage

- Location: `$XDG_CONFIG_HOME/olink/pins.json`, falling back to
  `~/.config/olink/pins.json` when `XDG_CONFIG_HOME` is unset.
- Format:

  ```json
  {"pins": ["origin", "pypi"]}
  ```

  A plain ordered list of catalog target names. Order is preserved to drive the
  top-of-list ordering.
- Pure stdlib (`json`, `os`, `pathlib`). **No new dependency.**

### Error handling

- Missing file → empty list (no error).
- Corrupt or unreadable file → treated as empty list, logged as a warning;
  the TUI never crashes.
- Unknown names in the file (e.g. a target later removed from the catalog) are
  simply ignored at display time — they match no `TargetItem`. The file is left
  as-is; no destructive rewrite on load.
- Write failures (e.g. read-only config dir) are surfaced in the status bar; the
  in-memory pin state still updates for the session so the TUI stays usable.

## Code shape

Follows the existing feature-grouped layout. Each unit is independently
understandable and regenerable.

### `src/olink/core/pins.py` (new)

Pure persistence logic, no coupling to the TUI.

- `config_dir() -> Path` — resolves `$XDG_CONFIG_HOME/olink` or
  `~/.config/olink`.
- `load_pins() -> list[str]` — reads `pins.json`, returns ordered names;
  returns `[]` on missing/corrupt.
- `save_pins(pins: list[str]) -> None` — writes `pins.json`, creating the config
  dir as needed.
- `toggle_pin(name: str) -> list[str]` — loads, toggles `name`, saves, returns
  the new list. (Appends on pin so newest pin lands at the bottom of the pinned
  group; removes on unpin.)

### `src/olink/tui/models.py`

- `TargetItem` gains `pinned: bool = False`.
- A helper orders a `list[TargetItem]` pinned-first (pinned in pin-order, rest
  keeping their existing alphabetical order).

### `src/olink/tui/app.py`

- Load pins into `self.pinned` (a set for membership + the ordered list for
  sort) on init.
- New `p` binding → `action_toggle_pin`: toggle the selected item's name,
  persist via `save_pins`, refresh the list, keep the selection on the same
  target where possible.
- Apply pin-ordering in `_source()` so both modes and search inherit it.
- Write failures surface via the existing status-bar error path.

### `src/olink/tui/widgets.py`

- Render the `★` marker for pinned items.

### Header

- Update `HEADER_TEXT` to include the `p: pin` hint.

## Testing

### `tests/core/test_pins.py` (new)

- Missing file → `[]`.
- `save_pins` / `load_pins` round-trip preserves order.
- Corrupt JSON → `[]` (no raise).
- `XDG_CONFIG_HOME` honored (monkeypatched to a tmp dir).
- `toggle_pin` adds then removes.

### `tests/tui/test_tui.py`

- Pinned targets sort to the top.
- `p` toggles pin state and persists to disk.
- `★` marker shown for pinned items.
- `available` mode hides a pin that is not available for the current project.

## Out of scope (YAGNI)

- Per-project pins.
- CLI pin commands / opening pins directly from the CLI.
- Reordering pins within the pinned group.
- Any limit on the number of pins.
