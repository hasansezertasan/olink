Usage
=====

As a library
------------

Look up the installed distribution version:

.. literalinclude:: examples/version_lookup.py
   :language: python
   :caption: examples/version_lookup.py

For short interactive snippets embedded in prose, the ``docs-doctest`` task
executes ``>>>`` blocks too:

.. doctest::

   >>> from olink.__metadata__ import PROJECT_NAME
   >>> PROJECT_NAME
   'olink'

As a command-line tool
----------------------

Open the page you want for the current project by naming a target:

.. code-block:: sh

   olink open origin     # Open the remote's homepage
   olink open issues     # Open the issues page
   olink open pypi       # Open the PyPI project page
   olink url pypi        # Print the URL without opening it
   olink list            # List targets available for the current project
   olink list --all      # List every known target
   olink interactive     # Launch the TUI (needs the ``tui`` extra)
   olink --version       # Show the olink version

Every command accepts ``-d``/``--directory`` to point olink at a different
project directory:

.. code-block:: sh

   olink open -d /path/to/project issues

``open``, ``url``, ``list``, ``version`` and ``info`` accept ``--json`` for
scripts and agents. Stdout is then exactly one JSON document, errors included
(``{"error": {"type": ..., "message": ...}}``), and failures exit with a
distinct code per error type: ``3`` unknown target, ``4`` bad directory, ``5``
not a git repo, ``6`` no remote, ``7`` missing project metadata, ``8``
unsupported on this platform, ``9`` unknown git host.

.. code-block:: sh

   olink url pypi --json
   olink list --json

Or invoke it programmatically from Python:

.. literalinclude:: examples/cli_usage.py
   :language: python
   :caption: examples/cli_usage.py

As a TUI
--------

Run ``olink`` with no target to launch the interactive terminal user interface
(requires the ``tui`` extra — install with ``uv tool install 'olink[tui]'``):

.. code-block:: sh

   olink
