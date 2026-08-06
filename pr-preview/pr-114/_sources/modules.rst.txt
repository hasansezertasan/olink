.. A 7-character "=" underline (the length of "Modules") is treated as a
   merge-conflict separator by ``git diff --check`` / ``check-merge-conflict``;
   keep this underline longer than the title to avoid the false positive.

Modules
=========

An overview of the packages that make up ``olink``.
The API reference below is generated automatically from the source docstrings.

Core (``olink.core``)
-----------------------------

Domain logic: git remote parsing, ecosystem detection, target definitions, the
target registry, custom exceptions, and pinned-target persistence.

.. automodule:: olink.core.project

.. automodule:: olink.core.targets

.. automodule:: olink.core.catalog

.. automodule:: olink.core.exceptions

.. automodule:: olink.core.pins

CLI (``olink.cli``)
-----------------------------

Typer command-line interface.

.. automodule:: olink.cli.app

TUI (``olink.tui``)
-----------------------------

Textual terminal user interface.

.. automodule:: olink.tui.app

.. automodule:: olink.tui.actions

.. automodule:: olink.tui.models

.. automodule:: olink.tui.widgets
