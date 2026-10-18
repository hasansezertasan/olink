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

**Update 2026-10-18:** the "not as committed plugin files" part is
superseded by [Plugin lives in this repo's `olink.yazi/`](#plugin-lives-in-this-repos-olinkyazi);
the wrapper design itself stands.

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

## Published from a separate plugin repo

**Id:** 6b476e7c-86e6-4d34-9cfc-1bd252e8fc5d
**Type:** decision
**Status:** superseded
**Superseded by:** 9d29f593-e1ac-408e-8a57-fd044c0cf5cb
**Evidence:** confirmed
**Source:** developer conversation, 2026-10-18
**Revisit when:** yazi changes how `ya pkg` resolves packages, or the plugin needs to ship in lockstep with olink releases

The plugin is published as `hasansezertasan/olink.yazi` (installed with
`ya pkg add hasansezertasan/olink`). `docs/examples/yazi_plugin.lua` in this
repo stays the tested source of truth; the plugin repo's `main.lua` is a copy
of it plus a `@since` annotation, and changes are made here first.

**Reason:** a single-plugin repo named `<name>.yazi` is yazi's convention, and
the plugin only calls the `olink` binary, so its versions need not follow
olink's. A separate repo also keeps `ya pkg` pins from tracking every olink
commit (including dependency churn) and keeps a `*.yazi` directory out of a
Python repository.

**Rejected alternative:** a subdirectory of this repo, installed with
`ya pkg add hasansezertasan/olink:<subdir>`. Rejected because of the pin
churn and the foreign directory above. It would have kept the plugin and its
lupa tests together; the copy-from-here step trades that for decoupling.
How yazi resolves the subdirectory name for a one-plugin repo was not verified.

**Consequence:** the copy into the plugin repo is manual for now, so the two
can drift until a release step or CI sync exists.

**See:** yazi.md#wrapper-plugin-over-native-port — 5a9fb28a-305c-4aa6-8976-4aefc6ef99da — as of 2026-10-18

## Plugin lives in this repo's `olink.yazi/`

**Id:** 9d29f593-e1ac-408e-8a57-fd044c0cf5cb
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** developer conversation, 2026-10-18; install behavior checked by running `ya pkg add` against a throwaway repo
**Revisit when:** `ya pkg` supports nested subdirectories, or the plugin needs versions independent of olink

The plugin is `olink.yazi/` at the root of this repository (`main.lua`,
`README.md`, `LICENSE`), installed with `ya pkg add hasansezertasan/olink:olink`.
`olink.yazi/main.lua` is the only copy: the docs include it verbatim and the
lupa tests execute it. The short-lived `hasansezertasan/olink.yazi` repo and
its v0.1.0 release were deleted.

**Reason:** the plugin's real coupling is olink's `olink list` text layout and
root markers; keeping the file beside the CLI means CI catches drift before a
release, with no copy step and no sync check to maintain.

**Rejected alternative:** a separate `olink.yazi` repo with a copy-from-here
release step (the previous decision). Rejected because the manual copy could
drift from the tested file, and a sync check would be extra machinery for one file.

**Consequence:** `ya pkg` requires the package directory at the repository
root, named `<name>.yazi` (a nested path such as `yazi/olink` fails with
"must be in kebab-case"), so a `olink.yazi/` directory sits in the root of a
Python repository. The plugin has no version of its own, `ya pkg` pins track
olink commits, and `olink.yazi/README.md` mentions olink 0.3.0 as the minimum.

**See:** yazi.md#published-from-a-separate-plugin-repo — 6b476e7c-86e6-4d34-9cfc-1bd252e8fc5d — as of 2026-10-18
