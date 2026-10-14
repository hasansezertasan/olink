Yazi integration
================

`yazi <https://yazi-rs.github.io/>`_ is a terminal file manager with a Lua
plugin system. olink maps well onto it as a thin **wrapper** plugin: the Lua
side only discovers the project directory, shows a menu, and shells out to
the ``olink`` binary. No URL logic is ported, so the plugin never drifts when
new targets are added. Tested against yazi 26.9.1; the APIs used are
``ya.sync``, ``ya.which``, ``ya.notify``, ``ya.clipboard``, ``ya.emit``,
``ya.quote``, ``Command:output`` and ``fs.cha``.

How it works
------------

1. Yazi gives the plugin the current tab's directory (``cx.active.current.cwd``).
2. The plugin walks up to the project root — olink only works from the root —
   and runs ``olink list -d <root>`` to learn which targets exist there.
3. The target names become a ``ya.which`` key menu (names always fit the
   menu's column layout); the pick shows a confirm dialog with the full
   description and the resolved URL, and confirming runs
   ``olink open <target> -d <root>`` (or ``olink url`` + clipboard with
   ``--copy``, no dialog).

Requirements
------------

- The ``olink`` CLI on ``PATH``.
- A yazi new enough for ``ya.which`` (any recent release; 26.9.1 verified).

Install
-------

Copy the sketch below to ``~/.config/yazi/plugins/olink.yazi/main.lua`` and
bind it in ``~/.config/yazi/keymap.toml``:

.. code-block:: toml

   [[mgr.prepend_keymap]]
   on = ["g", "o"]
   run = "plugin olink"
   desc = "Open project links with olink"

   [[mgr.prepend_keymap]]
   on = ["g", "O"]
   run = "plugin olink --copy"
   desc = "Copy project link URL with olink"

Press ``g o`` while browsing a project to open a link, ``g O`` to copy the
URL instead. Outside a project (no root markers found) the plugin notifies
instead of failing silently.

Plugin sketch
-------------

The sketch below is the tested file ``docs/examples/yazi_plugin.lua``,
included verbatim — what you read here is what the tests execute:

.. literalinclude:: examples/yazi_plugin.lua
   :language: lua
   :caption: examples/yazi_plugin.lua

Testing
-------

``tests/test_yazi_plugin.py`` keeps this page honest:

- the ``literalinclude`` above must reference the example file, so docs and
  code cannot drift;
- the TOML keymap snippet must parse;
- the Lua file is compiled and its entry point is executed inside
  `lupa <https://github.com/scoder/lupa>`_ (an in-process Lua runtime, so
  this runs on every CI OS with no system dependency) against live
  ``olink list`` / ``olink url`` output from a fixture project — covering
  the open path with its confirm dialog, dialog dismissal, ``--copy``,
  menu dismissal, the no-project-root case, and olink failure.

Notes
-----

- **Picker:** the which-key menu shows target names only, because its
  column layout chops longer labels mid-word and nothing may be shortened
  by the plugin. The full description and resolved URL appear on the
  confirm dialog instead — everything stays inside yazi's own UI.

- **Why parse the text output?** ``olink list --json`` exists, but decoding
  it in Lua needs either ``jq`` on ``PATH`` or a JSON library; the
  ``name - description`` lines parse with one pattern and keep the plugin
  dependency-free. If olink ever changes that text layout, switch the
  ``parse_list`` step to ``--json``.
- **Multi-ecosystem projects:** the listed name (e.g. ``deps``) opens fine
  when one ecosystem is detected; with several, pass the listed name through
  — explicit ``target:ecosystem`` suffixes from ``olink list --all`` are a
  future refinement, not handled in this sketch.
- **More targets than keys:** the menu caps at the key pool (36 entries);
  ``olink list`` for one project stays well below that in practice.
- **No TUI here:** ``olink interactive`` is replaced by yazi's own
  ``ya.which`` menu — the right trade, since yazi *is* the interface.
