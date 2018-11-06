import pytest
import pytoml
import os

from pasee.identity_providers.utils import get_identity_provider_with_capability


@pytest.fixture
def settings():
    settings = pytoml.loads(
        """
[[identity_providers]]
name = "Let's test with json"
implementation = "json.dumps"
capabilities = ["register-user"]

[[identity_providers]]
name = "twitter"
"""
    )
    settings["idps"] = {idp["name"]: idp for idp in settings["identity_providers"]}
    return settings


def test_get_identity_provider_with_capability(settings):
    assert "Let's test with json" in get_identity_provider_with_capability(
        settings, "register-user"
    )


def test_get_identity_provider_with_capability_not_found(settings):
    assert get_identity_provider_with_capability(settings, "delete-user") is None
