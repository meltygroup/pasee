import pytest

from pasee import Unauthorized


def test_unauthorized_exception():
    with pytest.raises(Unauthorized):
        raise Unauthorized(reason="for test")
