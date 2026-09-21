"""Tests for the package's runnable entrypoint (``python -m olink``)."""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.machinery import ModuleSpec
    from types import ModuleType


def test_main_is_callable() -> None:
    """The package exposes a callable ``main()`` entrypoint.

    Every standalone-executable build (launcher / freezer / compiler — see
    ADR-007) targets ``olink.__main__:main``, so this pins the
    contract that the symbol exists and is callable for whichever component is
    enabled, and that the active branch's component import actually resolves.
    The module is imported (not executed as ``__main__``), so a runnable
    component's blocking ``main()`` (server loop, mainloop, ...) is never invoked.
    """
    main_module = importlib.import_module("olink.__main__")

    assert callable(main_module.main)
    # The console root is resolved through ``_load_console_root`` (so a missing
    # root dependency stays actionable rather than a bare traceback); calling it
    # here performs the same import ``main()`` would and pins the wiring.
    assert callable(vars(main_module)["_load_console_root"]())


@pytest.mark.parametrize("dependency", ["typer"])
def test_console_root_reports_missing_launcher_dependency(
    dependency: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing root dependency is reported actionably, not as a bare traceback.

    Every module parametrized here is imported at the console root's module
    scope -- ``typer`` by the root itself, ``pydantic``/``pydantic_settings``
    transitively through ``core.logging_setup`` -> ``core.config`` -- so each one
    fails before the component-dependency guard inside ``cli/app.py`` exists.

    Given:
        - An environment out of sync with the installed package, so one of the
          root's own dependencies cannot be imported -- what a ``copier update``
          that adds the shared launcher (or enables settings) leaves behind until
          ``uv sync``.
    When:
        - ``__main__`` loads the console root, as bare ``olink`` does.
    Then:
        - It exits 1 with a message naming the module and ``uv sync``, and no
          traceback.
    """
    main_module = importlib.import_module("olink.__main__")
    monkeypatch.setitem(sys.modules, dependency, None)
    # Drop the package's own modules so the guarded import chain runs again.
    prefix = "olink."
    for cached in [name for name in sys.modules if name.startswith(prefix)]:
        monkeypatch.delitem(sys.modules, cached, raising=False)

    with pytest.raises(SystemExit) as excinfo:
        _ = vars(main_module)["_load_console_root"]()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert dependency in err
    assert "uv sync" in err
    assert "Traceback" not in err


_NESTED_ROOT_DEP_MESSAGE = "No module named 'transitive_dep'"


class _NestedRootDependencyMissingFinder:
    """Simulate a root dependency installed without a mandatory sub-dependency."""

    def __init__(self, target_module: str) -> None:
        self._target = target_module

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """Fail the preflight import with the nested dependency's name.

        Raises:
            ModuleNotFoundError: Naming ``transitive_dep`` when the root is imported.
        """
        del path, target
        if fullname == self._target:
            raise ModuleNotFoundError(_NESTED_ROOT_DEP_MESSAGE, name="transitive_dep")
        return None


@pytest.mark.parametrize("dependency", ["typer"])
def test_console_root_reports_missing_nested_root_dependency(
    dependency: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A nested failure while preflighting a root dependency is attributed to it."""
    main_module = importlib.import_module("olink.__main__")
    finder = _NestedRootDependencyMissingFinder(dependency)
    # The stub intercepts only its own target, so an unrelated import still
    # resolves normally -- and the pass-through arm stays exercised.
    assert finder.find_spec("json", None) is None
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])
    monkeypatch.delitem(sys.modules, dependency, raising=False)
    prefix = "olink."
    for cached in [name for name in sys.modules if name.startswith(prefix)]:
        monkeypatch.delitem(sys.modules, cached, raising=False)

    with pytest.raises(SystemExit) as excinfo:
        _ = vars(main_module)["_load_console_root"]()

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert dependency in err
    assert "uv sync" in err
    assert "Traceback" not in err


def test_console_root_preserves_unrelated_import_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing module that is not a root dependency keeps its own diagnostics.

    Given:
        - Loading the console root fails for an unrelated reason (here the
          ``cli`` package itself), which is an application defect rather than an
          out-of-sync environment.
    When:
        - ``__main__`` loads the console root.
    Then:
        - The original ``ModuleNotFoundError`` propagates and is never relabelled
          as something ``uv sync`` would fix.
    """
    main_module = importlib.import_module("olink.__main__")
    monkeypatch.setitem(sys.modules, "olink.cli", None)

    with pytest.raises(ModuleNotFoundError, match=r"olink\.cli"):
        _ = vars(main_module)["_load_console_root"]()

    assert "uv sync" not in capsys.readouterr().err


#: A name no distribution claims, so only the finder below can resolve it.
_BROKEN_MODULE = "broken_preflight_target"
_BROKEN_MODULE_MESSAGE = "cannot import name 'x' from a partially initialized module"


class _BrokenModuleFinder:
    """Simulate a dependency that is installed but whose import raises."""

    @staticmethod
    def find_spec(
        fullname: str, path: Sequence[str] | None, target: ModuleType | None = None
    ) -> ModuleSpec | None:
        """Fail the sentinel import with a *nameless* ``ImportError``.

        Raises:
            ImportError: Carrying no module name, the shape a broken install
                raises and that exact-name matching cannot classify.
        """
        del path, target
        if fullname == _BROKEN_MODULE:
            raise ImportError(_BROKEN_MODULE_MESSAGE)
        return None


def test_preflight_names_a_dependency_that_fails_to_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A nameless ``ImportError`` is re-raised naming the preflighted module.

    Given:
        - A dependency present on disk whose own import raises without naming a
          module, i.e. a broken rather than a missing install.
    When:
        - ``__main__`` preflights it.
    Then:
        - It becomes a ``ModuleNotFoundError`` carrying that module's name, so
          the guard's exact-match rule can classify it.
    """
    main_module = importlib.import_module("olink.__main__")
    finder = _BrokenModuleFinder()
    # The stub intercepts only its own target, so an unrelated import still
    # resolves normally -- and the pass-through arm stays exercised.
    assert finder.find_spec("json", None) is None
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])

    with pytest.raises(ModuleNotFoundError) as excinfo:
        vars(main_module)["_preflight"](_BROKEN_MODULE)

    assert excinfo.value.name == _BROKEN_MODULE
