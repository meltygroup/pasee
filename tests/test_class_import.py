"""Tests for the class importer.
"""


import pytest

from pasee.utils import import_class


def test_import_authorization_backend():
    """Test importing authorization backend
    """
    with pytest.raises(ImportError):
        import_class("helloworldxddd~~~")
    with pytest.raises(ImportError):
        import_class("my.dummy.path")
    with pytest.raises(ImportError):
        import_class("authorization_backend.test_backend.UnknownClass")
