# Yazi integration

## Wrapper plugin over native port

**Id:** 5a9fb28a-305c-4aa6-8976-4aefc6ef99da
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** developer conversation, 2026-10-14

The yazi integration is a thin wrapper plugin: Lua discovers the project
directory and shows a menu, then shells out to the `olink` binary. No URL
logic is ported to Lua. Documented as a sketch in `docs/yazi.rst`, not as
committed plugin files, since yazi plugins ship via `ya pkg`, not from
this repo.

**Reason:** porting the registry URL shapes to Lua would create a second
copy of every target to maintain; the wrapper never drifts when targets
are added. `olink list` plus `-d`/`--json` already provide the
machine-readable contract a wrapper needs.

**Rejected alternative:** native Lua reimplementation of the target URLs.
Rejected because it duplicates the registry and rots independently.

**Rejected alternative:** parsing `olink list --json` in Lua. Rejected
because it needs `jq` on `PATH` or a JSON library; the
`name - description` text lines parse with one pattern and keep the plugin
dependency-free. If olink ever changes that text layout, switch this step
to `--json`.

**Rejected alternative:** `ya.input` picker and shipping `olink interactive`.
Rejected because `ya.which` fits single-keystroke target selection and yazi
itself is the interface, so the Textual TUI has no role there.

**Consequence:** target selection shows names only in the `ya.which` menu
(full labels chop in its column layout and nothing may be shortened by the
plugin), with the full description and resolved URL on a confirm dialog —
everything stays inside yazi's UI. A fullscreen fzf picker was tried and
reverted: leaving yazi's interface for selection broke the flow it was
meant to speed up.
