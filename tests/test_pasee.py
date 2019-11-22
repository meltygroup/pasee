import pytest

from pasee.__main__ import load_conf
from pasee import MissingSettings
import mocks


def test_load_conf():
    """Test the configuration logging
    """
    with pytest.raises(MissingSettings):
        load_conf("nonexistant.toml")
    config = load_conf("tests/test-settings.toml")
    assert config["host"] == "0.0.0.0"
    load_conf(settings_path="tests/test-settings.toml", host="127.0.0.1", port=4242)


def test_load_conf__none_in_parameter(monkeypatch):
    monkeypatch.setattr("pasee.__main__.os.path.join", mocks.join)
    config = load_conf(None)
    assert config["host"] == "0.0.0.0"


def test_load_conf__missing_variables_in_conf(monkeypatch):
    with pytest.raises(MissingSettings):
        config = load_conf("tests/test-settings-missing-values.toml")
