# Platforms

## URL suffixes as data, not classes

**Id:** 5125fd5f-dff1-4ae5-8b5e-6ce89ef20447
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-02-01; `core/targets.py` (`PLATFORM_URLS`)

Per-platform page paths live in the `PLATFORM_URLS` dict. Before this, a
`platforms/` directory held five files with platform classes whose methods
only concatenated base URLs with suffixes — about 100 lines for what is
configuration data.

**Reason:** the "logic" was pure input-to-output mapping with no
conditionals, loops, or state, so a dict is clearer, shorter, and easier to
extend (one line per platform) and to test (assert values, no mocks).

**Rejected alternative:** consolidating into a single `platforms.py` or
moving the classes into `core/`. Both kept the class hierarchy; rejected
once the challenge "what is wrong with inlining it as a dict" had no good
answer — the hesitation was familiarity bias toward classes, not a technical
need. This incident is the origin of the project's "Data Over Classes"
rule in `AGENTS.md`.
