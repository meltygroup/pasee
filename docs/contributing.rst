Contributing
============

Quickstart
----------

To install dev dependencies, create a venv and run::

  pip install flit
  flit install --symlink

And run kisee using::

  pasee  # or python -m pasee


Releasing
---------

Our version scheme is `calver <https://calver.org/>`__, specifically
``YY.MM.MICRO``, so please update it in ``pasee/__init__.py`` (single
place), git tag, commit, and push.

Then to release we're using `flit <https://flit.readthedocs.io>`__::

  flit publish
