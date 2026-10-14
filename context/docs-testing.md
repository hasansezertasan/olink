# Docs testing

## Docs Lua runs under lupa, not luajit

**Id:** d6db664b-86c0-4dd3-a41b-e02712a0a758
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** developer conversation, 2026-10-14; `tests/test_yazi_plugin.py`, `pyproject.toml` (test group)

The yazi plugin sketch in `docs/yazi.rst` is a tested file
(`docs/examples/yazi_plugin.lua`, pulled in verbatim via `literalinclude`)
executed by `tests/test_yazi_plugin.py` inside lupa — an in-process Lua
runtime pinned in the test group — against live `olink list`/`url` output
from a fixture project.

**Reason:** a `luajit` system dependency with a skip-guard would skip on
exactly the machines that need the gate (CI, Windows), and skipped bodies
still count as missed lines under the 99% coverage floor. lupa runs
everywhere the test suite runs with no system dependency.

**Rejected alternative:** shelling out to a `luajit` binary, skipping when
absent. Rejected because environment-conditional coverage is a hole in the
gate, not a convenience.

**Quirk on record:** lupa bundles Lua 5.5, whose parser rejects long
brackets containing `=` as table-constructor keys
(`{[===[a]===] = 1}` fails; `[[a]]` keys and long-bracket values are
fine). The test's generated canned file therefore uses quoted keys. The
plugin file itself uses only 5.1-compatible constructs, so it is unaffected
— yazi ships LuaJIT/5.4, not 5.5.
