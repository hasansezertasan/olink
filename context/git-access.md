# Git access

## File reads over git subprocess

**Id:** 5bfad594-a42e-4ddb-98ec-14a53a37de7c
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-02-01; `core/project.py`

olink reads `.git/config` directly with `configparser` instead of spawning
`git` subprocesses (`rev-parse`, `remote get-url`). The reader handles the
edge cases itself: worktree/submodule checkouts where `.git` is a file
carrying a `gitdir:` pointer.

**Reason:** ~50ms of subprocess overhead per call drops below 1ms, and
there is no dependency on a `git` binary being installed.

**Rejected alternative:** shelling out to `git`. Rejected for speed and
dependency weight; git's own edge-case handling was the thing lost, so the
`gitdir:` resolution is the load-bearing part of this decision.

**Limitation, then and now:** the 2026-02-01 note recorded no support for
`[url].insteadOf` rewrites or `[include]` directives. `insteadOf` support
was added later (PR #8, hardened in the 2026-04-29 pass with longest-prefix
matching per git's algorithm) so shorthand remotes like `github:owner/repo`
resolve; `[include]` remains unsupported.
