import pytest

import pasee.pasee as pasee


def test_load_conf():
    """Test the configuration logging
    """
    with pytest.raises(UnboundLocalError):
        pasee.load_conf("settings.toml")
    config = pasee.load_conf("tests/test-settings.toml")
    assert config["host"] == "0.0.0.0"
