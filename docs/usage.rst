Usage
=====

As a library
------------

To use ``olink`` in a project:

.. code-block:: python

   import olink

As a command-line tool
----------------------

Open the page you want for the current project by naming a target:

.. code-block:: sh

   olink origin          # Open the remote's homepage
   olink issues          # Open the issues page
   olink pypi            # Open the PyPI project page
   olink --list          # List targets available for the current project
   olink --list-all      # List every known target
   olink --version       # Show the olink version

Pass ``-n``/``--dry-run`` to print the resolved URL instead of opening it, and
``-d``/``--directory`` to point olink at a different project directory:

.. code-block:: sh

   olink -n pypi
   olink -d /path/to/project issues

As a TUI
--------

Run ``olink`` with no target to launch the interactive terminal user interface
(requires the ``tui`` extra — install with ``uv tool install 'olink[tui]'``):

.. code-block:: sh

<<<<<<< before updating
   olink
=======
   olink interactive
>>>>>>> after updating
