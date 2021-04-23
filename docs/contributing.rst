Contributing
============

Quickstart
----------

To install dev dependencies, create a venv and run::

  pip install . -r requirements-dev.txt

And run pasee using::

  pasee  # or python -m pasee


Releasing
---------

Our version scheme is `calver <https://calver.org/>`__, specifically
``YY.MM.MICRO``, so please update it in ``pasee/__init__.py`` (single
place), git tag, commit, and push.

Then to release we're using `build <https://pypa-build.readthedocs.io/>`__ and `twine <https://twine.readthedocs.io/>`__::

  pip install build twine
  python -m build
  twine upload dist/*
