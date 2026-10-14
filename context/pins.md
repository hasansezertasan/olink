# Pins

## Pins are global and TUI-only

**Id:** df38d92e-1a20-4b91-b086-655ddac9d709
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-08-03 (PR #70); `core/pins.py`

Pinned targets persist machine-wide in `$XDG_CONFIG_HOME/olink/pins.json`
and float to the top of the TUI list across projects. Pinning is wired
only in the TUI (`p` key); the CLI has no pin concept.

**Reason:** pins are personal bookmarks, so per-project storage would
fragment them; a globally pinned target that does not apply to the current
project simply stays hidden rather than leaking across. The CLI stays a
stateless one-shot — bookmarks belong to the interactive browser, not to
scripted invocation.

**Rejected alternative:** per-project pin storage. Rejected because the
same target pinned in five checkouts is one bookmark, not five.
