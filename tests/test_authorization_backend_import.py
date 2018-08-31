"""Tests for the identification provider class
"""


import pytest

from pasee.groups.backend import import_authorization_backend


def test_import_authorization_backend():
    """Test importing authorization backend
    """
    with pytest.raises(ImportError):
        import_authorization_backend("helloworldxddd~~~")
    with pytest.raises(ImportError):
        import_authorization_backend("my.dummy.path")
    with pytest.raises(ImportError):
        import_authorization_backend("authorization_backend.test_backend.UnknownClass")
