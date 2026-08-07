Installation
============

Possible extras:

- ``cli``: Installs typer and adds ``olink`` as a command.
- ``tui``: Installs textual and adds ``olink-tui`` as a command.
- ``all``: Installs all extras if available.

Stable release
--------------

To install ``olink``, run this command in your terminal:

.. code-block:: sh

   uv add olink

Or if you prefer to use ``pip``:

.. code-block:: sh

   pip install olink

From source
-----------

The source files for ``olink`` can be downloaded from the
`GitHub repo <https://github.com/hasansezertasan/olink>`_.

You can either clone the public repository:

.. code-block:: sh

   git clone https://github.com/hasansezertasan/olink.git

Or download the
`tarball <https://github.com/hasansezertasan/olink/tarball/main>`_:

.. code-block:: sh

   mkdir olink
   curl -fL https://github.com/hasansezertasan/olink/tarball/main | tar -xz --strip-components=1 -C olink

Once you have a copy of the source, you can install it with:

.. code-block:: sh

   cd olink
   uv pip install .
