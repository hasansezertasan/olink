# Error handling

## Custom exception hierarchy kept

**Id:** 272d1e53-b5da-4e9f-84d6-c8c79a188e7f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** project journal (JOURNAL.md), 2026-02-01; `core/exceptions.py`, `cli/app.py`

olink keeps its own hierarchy (`OlinkError` and subclasses such as
`NotGitRepoError`, `UnknownTargetError`) instead of raising standard
exceptions.

**Reason:** the CLI catches `OlinkError` to print clean user-facing errors
with typed exit codes, while letting anything else crash with a stack
trace — programming bugs are never swallowed as "user errors". Tests gain
precision too: `pytest.raises(NoRemoteError)` pins the exact failure path
instead of possibly masking an unrelated `KeyError`.

**Rejected alternative:** standard `ValueError`/`RuntimeError`. Rejected
because one shared type cannot separate expected user errors from bugs at
the CLI boundary.
