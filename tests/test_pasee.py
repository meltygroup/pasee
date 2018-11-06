import pytest

from pasee import pasee
from pasee import MissingSettings


def test_load_conf():
    """Test the configuration logging
    """
    with pytest.raises(MissingSettings):
        pasee.load_conf("nonexistant.toml")
    config = pasee.load_conf("tests/test-settings.toml")
    assert config["host"] == "0.0.0.0"
