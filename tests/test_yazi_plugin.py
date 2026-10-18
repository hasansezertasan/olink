"""Tests for the yazi plugin sketch embedded in the documentation."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import lupa
import pytest
from typer.testing import CliRunner

from olink.cli.app import app
from tests.conftest import copy_repo_fixture, init_git_with_config

if TYPE_CHECKING:
    from collections.abc import Callable

DOCS_DIR = Path(__file__).parents[1] / "docs"
YAZI_RST = DOCS_DIR / "yazi.rst"
LUA_EXAMPLE = DOCS_DIR.parent / "olink.yazi" / "main.lua"
HARNESS = Path(__file__).parent / "fixtures" / "yazi_harness.lua"

runner = CliRunner()


@pytest.fixture
def fixture_project(temp_dir: str) -> str:
    """Build a git repo with a package manifest for live CLI output."""
    init_git_with_config("github_https", temp_dir)
    copy_repo_fixture("python_project", temp_dir)
    return temp_dir


def _lua_block(value: str) -> str:
    """Wrap text in long brackets that cannot collide with URLs or prose."""
    return f"[===[{value}]===]"


def _write_canned(path: Path, project: str) -> list[str]:
    """Capture live `list`/`url` output into a Lua file; return target names."""
    listed = runner.invoke(app, ["list", "--json", "-d", project])
    assert listed.exit_code == 0
    names = [target["name"] for target in json.loads(listed.stdout)["targets"]]
    assert names, "fixture project must expose at least one target"
    urls = {}
    for name in names:
        resolved = runner.invoke(app, ["url", name, "-d", project])
        assert resolved.exit_code == 0
        urls[name] = resolved.stdout.strip()
    text = runner.invoke(app, ["list", "-d", project])
    assert text.exit_code == 0
    entries = "\n".join(f'  ["{name}"] = {_lua_block(url)},' for name, url in urls.items())
    path.write_text(
        f"return {{ list = {_lua_block(text.stdout)},\nurls = {{\n{entries}\n}} }}\n",
        encoding="utf-8",
    )
    return names


@dataclass(frozen=True)
class _HarnessOptions:
    """Knobs for one harness run (mirrors the Lua globals it sets)."""

    copy: bool = False
    fail_list: bool = False
    fail_first: bool = False
    empty_first: bool = False
    which_idx: int | None = 1
    confirm: bool = True


@dataclass(frozen=True)
class _Observations:
    """Flat observations from one harness run; None means the call never happened."""

    first_desc: str | None = None
    emit_cmd: str | None = None
    clip: str | None = None
    notify_content: str | None = None
    notify_level: str | None = None
    confirm_shown: bool | None = None
    confirm_body: str | None = None


def _run_harness(
    cwd: str,
    canned: Path,
    options: _HarnessOptions | None = None,
    *,
    exists: Callable[[str], bool] | None = None,
) -> _Observations:
    """Execute the harness with stubbed yazi globals; return flat observations."""
    opts = options if options is not None else _HarnessOptions()
    runtime = lupa.LuaRuntime()
    env = runtime.globals()
    env["PLUGIN_PATH"] = str(LUA_EXAMPLE)
    env["CANNED_PATH"] = str(canned)
    env["CWD"] = cwd
    env["WHICH_IDX"] = opts.which_idx
    env["CONFIRM"] = opts.confirm
    env["COPY"] = opts.copy
    env["FAIL_LIST"] = opts.fail_list
    env["FAIL_FIRST"] = opts.fail_first
    env["EMPTY_FIRST"] = opts.empty_first
    env["TEST_EXISTS"] = exists if exists is not None else (lambda path: Path(path).exists())
    runtime.execute(HARNESS.read_text(encoding="utf-8"))
    seen = env["OBS"]
    return _Observations(
        first_desc=seen["first_desc"],
        emit_cmd=seen["emit_cmd"],
        clip=seen["clip"],
        notify_content=seen["notify_content"],
        notify_level=seen["notify_level"],
        confirm_shown=seen["confirm_shown"],
        confirm_body=seen["confirm_body"],
    )


class TestYaziDocs:
    """The yazi page must stay wired to the tested example file."""

    def test_page_includes_example_verbatim(self) -> None:
        """The literalinclude must reference the tested Lua file."""
        assert LUA_EXAMPLE.exists()
        assert ".. literalinclude:: ../olink.yazi/main.lua" in YAZI_RST.read_text(encoding="utf-8")

    def test_keymap_snippet_is_valid_toml(self) -> None:
        """The keymap block must parse and bind open plus copy."""
        text = YAZI_RST.read_text(encoding="utf-8")
        match = re.search(r"\.\. code-block:: toml\n\n((?:   .+\n|[ \t]*\n)+)", text)
        assert match is not None
        snippet = "\n".join(line[3:] for line in match.group(1).splitlines() if line.strip())
        bindings = tomllib.loads(snippet)["mgr"]["prepend_keymap"]
        assert [binding["run"] for binding in bindings] == [
            "plugin olink",
            "plugin olink -- --copy",
        ]


class TestYaziPluginLua:
    """The documented sketch must compile and behave against live CLI output."""

    def test_plugin_compiles(self) -> None:
        """Invalid Lua must fail here, not in a user's yazi session."""
        runtime = lupa.LuaRuntime()
        assert runtime.compile(LUA_EXAMPLE.read_text(encoding="utf-8")) is not None

    def test_open_target_from_subdirectory(self, tmp_path: Path, fixture_project: str) -> None:
        """Browsing a subdir still opens a target of the enclosing project."""
        subdir = Path(fixture_project) / "src"
        subdir.mkdir()
        canned = tmp_path / "canned.lua"
        names = _write_canned(canned, fixture_project)
        listed = runner.invoke(app, ["list", "--json", "-d", fixture_project])
        descriptions = {t["name"]: t["description"] for t in json.loads(listed.stdout)["targets"]}
        resolved = runner.invoke(app, ["url", names[0], "-d", fixture_project])
        url = resolved.stdout.strip()
        obs = _run_harness(str(subdir), canned)
        assert obs.first_desc == names[0]
        assert obs.confirm_shown is True
        body = obs.confirm_body
        assert body is not None
        assert descriptions[names[0]] in body
        assert url in body
        assert obs.emit_cmd == f"olink open '{names[0]}' -d '{fixture_project}'"
        assert obs.notify_content is None

    def test_dismissed_confirm_opens_nothing(self, tmp_path: Path, fixture_project: str) -> None:
        """Answering the confirm dialog with no must neither open nor notify."""
        canned = tmp_path / "canned.lua"
        _write_canned(canned, fixture_project)
        obs = _run_harness(fixture_project, canned, _HarnessOptions(confirm=False))
        assert obs.confirm_shown is True
        assert obs.emit_cmd is None
        assert obs.clip is None
        assert obs.notify_content is None

    def test_copy_target_url(self, tmp_path: Path, fixture_project: str) -> None:
        """--copy must clipboard without opening and without a confirm dialog."""
        canned = tmp_path / "canned.lua"
        names = _write_canned(canned, fixture_project)
        assert len(names) >= 2
        obs = _run_harness(fixture_project, canned, _HarnessOptions(which_idx=2, copy=True))
        resolved = runner.invoke(app, ["url", names[1], "-d", fixture_project])
        assert obs.clip == resolved.stdout.strip()
        assert obs.confirm_shown is None
        assert obs.emit_cmd is None
        notice = obs.notify_content
        assert notice is not None
        assert resolved.stdout.strip() in notice

    def test_dismissed_menu_does_nothing(self, tmp_path: Path, fixture_project: str) -> None:
        """Dismissing the menu must neither open nor notify."""
        canned = tmp_path / "canned.lua"
        _write_canned(canned, fixture_project)
        obs = _run_harness(fixture_project, canned, _HarnessOptions(which_idx=None))
        assert obs.confirm_shown is None
        assert obs.emit_cmd is None
        assert obs.clip is None
        assert obs.notify_content is None

    def test_no_project_root_notifies(self, tmp_path: Path) -> None:
        """Outside any project the plugin must explain instead of failing."""
        canned = tmp_path / "canned.lua"
        canned.write_text("return { list = '', urls = {} }\n", encoding="utf-8")
        obs = _run_harness(str(tmp_path), canned)
        assert obs.notify_level == "error"
        assert obs.emit_cmd is None

    def test_windows_style_root_walk(self, tmp_path: Path) -> None:
        """Backslash-separated paths must walk up to the project root too."""
        canned = tmp_path / "canned.lua"
        canned.write_text("return { list = '', urls = {} }\n", encoding="utf-8")
        present = {"C:\\proj\\.git", "C:\\proj\\pyproject.toml"}
        obs = _run_harness("C:\\proj\\src", canned, exists=lambda path: path in present)
        notice = obs.notify_content
        assert notice is not None
        assert "no olink targets" in notice

    def test_retries_past_broken_manifest(self, tmp_path: Path, fixture_project: str) -> None:
        """A manifest-only dir olink rejects must not hide a usable ancestor."""
        inner = Path(fixture_project) / "sub" / "inner"
        inner.mkdir(parents=True)
        (inner / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        canned = tmp_path / "canned.lua"
        names = _write_canned(canned, fixture_project)
        obs = _run_harness(str(inner), canned, _HarnessOptions(fail_first=True))
        assert obs.emit_cmd == f"olink open '{names[0]}' -d '{fixture_project}'"

    def test_git_boundary_stops_retry(self, tmp_path: Path, fixture_project: str) -> None:
        """A rejected repository must error, not open a parent's links."""
        inner = Path(fixture_project) / "sub"
        inner.mkdir()
        init_git_with_config("github_https", str(inner))
        canned = tmp_path / "canned.lua"
        _write_canned(canned, fixture_project)
        obs = _run_harness(str(inner), canned, _HarnessOptions(fail_first=True))
        notice = obs.notify_content
        assert notice is not None
        assert "boom" in notice
        assert obs.emit_cmd is None

    def test_retries_past_empty_target_list(self, tmp_path: Path, fixture_project: str) -> None:
        """An exit-zero empty list must retry upward like a failure does."""
        inner = Path(fixture_project) / "sub" / "inner"
        inner.mkdir(parents=True)
        (inner / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
        canned = tmp_path / "canned.lua"
        names = _write_canned(canned, fixture_project)
        obs = _run_harness(str(inner), canned, _HarnessOptions(empty_first=True))
        assert obs.emit_cmd == f"olink open '{names[0]}' -d '{fixture_project}'"

    def test_menu_cap_notifies(self, tmp_path: Path, fixture_project: str) -> None:
        """Beyond the key pool the menu must admit what it omits."""
        canned = tmp_path / "canned.lua"
        rows = [f"  t{i:02d} - Description number {i}" for i in range(1, 41)]
        entries = "\n".join(
            f'  ["t{i:02d}"] = {_lua_block(f"https://example.test/t{i:02d}")},'
            for i in range(1, 41)
        )
        canned.write_text(
            f"return {{ list = {_lua_block('\n'.join(rows))},\nurls = {{\n{entries}\n}} }}\n",
            encoding="utf-8",
        )
        obs = _run_harness(fixture_project, canned)
        assert obs.first_desc == "t01"
        notice = obs.notify_content
        assert notice is not None
        assert "36 of 40" in notice
        assert obs.emit_cmd == f"olink open 't01' -d '{fixture_project}'"

    def test_multi_ecosystem_suffix_passthrough(
        self, tmp_path: Path, temp_multi_ecosystem: str
    ) -> None:
        """Suffixed names from multi-ecosystem projects must open verbatim."""
        canned = tmp_path / "canned.lua"
        names = _write_canned(canned, temp_multi_ecosystem)
        suffixed = [name for name in names if ":" in name]
        assert suffixed, "multi-ecosystem project must list suffixed targets"
        picked = suffixed[0]
        obs = _run_harness(
            temp_multi_ecosystem, canned, _HarnessOptions(which_idx=names.index(picked) + 1)
        )
        assert obs.emit_cmd == f"olink open '{picked}' -d '{temp_multi_ecosystem}'"

    def test_olink_failure_notifies(self, tmp_path: Path, fixture_project: str) -> None:
        """A failing `olink list` must surface stderr, not an empty menu."""
        canned = tmp_path / "canned.lua"
        _write_canned(canned, fixture_project)
        obs = _run_harness(fixture_project, canned, _HarnessOptions(fail_list=True))
        notice = obs.notify_content
        assert notice is not None
        assert "boom" in notice
        assert obs.emit_cmd is None
