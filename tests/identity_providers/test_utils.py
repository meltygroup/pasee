import pytest
import pytoml

from pasee.identity_providers.utils import get_identity_provider_with_capability
from pasee.utils import enforce_authorization, Unauthorized, Unauthenticated

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEgLwEAlfrY/AJrS4bCzg2pEhXrT5Zu3cr
mVu3bgkvT/P7bsq4lu20o8kWQd/srSRCb7kvz9xQQMVLLemrebXZCA==
-----END PUBLIC KEY-----"""
PRIVATE_KEY = """-----BEGIN EC PRIVATE KEY-----
MHQCAQEEIJoeYe+EUPAPiQBTxvgV7qW0gMUbyGZLBKlIvXrarNIhoAcGBSuBBAAK
oUQDQgAEgLwEAlfrY/AJrS4bCzg2pEhXrT5Zu3crmVu3bgkvT/P7bsq4lu20o8kW
Qd/srSRCb7kvz9xQQMVLLemrebXZCA==
-----END EC PRIVATE KEY-----"""
ALGORITHM = "ES256"

WRONG_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJzdWIiOiJmb28iLCJqdGkiOjE1NDE2OTE0NzEuMDc1MjA5fQ.Du14Jn03DqXHVmbcZkJF-2X8JgU2F1IE82nkvVBeeC3wxOn21gk1zEq9XjrxHMqmBuhPgla5oP3Zx7qa6uYqmg"


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


def test_enforce_authorization__missing_authorization_header():
    with pytest.raises(Unauthenticated):
        assert enforce_authorization({}, {})


def test_enforce_authorization__no_scheme_value_value_pair_in_header():
    with pytest.raises(Unauthorized):
        assert enforce_authorization({"Authorization": "some-weird-token"}, {})


def test_enforce_authorization__wrong_scheme():
    with pytest.raises(Unauthorized):
        assert enforce_authorization({"Authorization": "not-expected-scheme token"}, {})


def test_enforce_authorization__not_valid_bearer_token():
    with pytest.raises(Unauthorized):
        assert enforce_authorization(
            {"Authorization": f"Bearer {WRONG_TOKEN}"},
            {"public_key": PUBLIC_KEY, "algorithm": ALGORITHM},
        )


def test_enforce_authorization__expired_token():
    expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJzdWIiOiJmb28iLCJleHAiOjE1NDE2OTI1NjAuNDU1Nzc5fQ.o3ZPwFmqJ3PLpxoZ854sHuu5ozD18J6kD7EdG2ospWSlovcgxGvSo65Hdgd8_RPHUDDJu4RZ4FwkyT1VTFRi_A"
    with pytest.raises(Unauthorized):
        assert enforce_authorization(
            {"Authorization": f"Bearer {expired_token}"},
            {"public_key": PUBLIC_KEY, "algorithm": ALGORITHM},
        )
