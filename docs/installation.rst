Installation
============

``olink`` is an end-user application, not a library, so install
it as a standalone tool rather than as a project dependency. Its primary entry
point is the ``olink`` command.

Stable release
--------------

Install ``olink`` into an isolated environment with your
preferred tool installer:

.. code-block:: sh

   uv tool install olink

.. code-block:: sh

   pipx install olink

Or run it without installing:

.. code-block:: sh

   uvx olink

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
   uv tool install .
