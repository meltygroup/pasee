from asyncio import run
import json

import aiohttp
from aioresponses import aioresponses
import jwt
import pytest

from pasee.identity_providers.kisee import KiseeIdentityProvider


PRIVATE_KEY = """
-----BEGIN EC PRIVATE KEY-----
MHQCAQEEIJJaLOWE+5qg6LNjYKOijMelSLYnexzLmTMvwG/Dy0r4oAcGBSuBBAAK
oUQDQgAEE/WCqajmhfppNUB2uekSxX976fcWA3bbdew8NkUtCoBigl9lWkqfnkF1
8H9fgG0gafPhGtub23+8Ldulvmf1lg==
-----END EC PRIVATE KEY-----"""

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEE/WCqajmhfppNUB2uekSxX976fcWA3bb
dew8NkUtCoBigl9lWkqfnkF18H9fgG0gafPhGtub23+8Ldulvmf1lg==
-----END PUBLIC KEY-----"""


@pytest.fixture
def provider():
    return KiseeIdentityProvider(
        {
            "settings": {"public_keys": [PUBLIC_KEY]},
            "endpoint": "http://kisee.example.com/",
        }
    )


@pytest.fixture
def test_token():
    return jwt.encode(
        {"iss": "test", "sub": "toto", "jti": "42"}, PRIVATE_KEY, algorithm="ES256"
    ).decode("utf8")


@pytest.fixture
def fake_kisee():
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://kisee.example.com/",
            status=200,
            body=json.dumps(
                {"actions": {"create-token": {"href": "http://kisee.example.com/jwt/"}}}
            ),
        )
        yield mocked


def test_endpoint_discovery(provider, fake_kisee):
    assert run(provider.get_endpoint()) == "http://kisee.example.com/"
    for _ in range(3):
        assert (
            run(provider.get_endpoint("create-token"))
            == "http://kisee.example.com/jwt/"
        )


def test_name(provider):
    assert provider.get_name() == "kisee"


def test_kisee_idp_succeed(provider, test_token, fake_kisee):
    fake_kisee.post(
        "http://kisee.example.com/jwt/",
        status=201,
        body=json.dumps({"tokens": [test_token]}),
    )
    claims = run(provider.authenticate_user({"login": "toto", "password": "toto"}))
    assert claims["sub"] == "kisee-toto"


def test_kisee_idp_missing_field(provider, test_token, fake_kisee):
    fake_kisee.post(
        "http://kisee.example.com/jwt/",
        status=201,
        body=json.dumps({"tokens": [test_token]}),
    )
    with pytest.raises(aiohttp.web_exceptions.HTTPBadRequest):
        run(provider.authenticate_user({"login": "toto"}))


def test_kisee_idp_bad_token(provider, test_token, fake_kisee):
    fake_kisee.post(
        "http://kisee.example.com/jwt/",
        status=201,
        body=json.dumps({"tokens": [test_token[::-1]]}),
    )
    with pytest.raises(aiohttp.web_exceptions.HTTPInternalServerError):
        run(provider.authenticate_user({"login": "toto", "password": "toto"}))


def test_kisee_idp_bad_password(provider, fake_kisee):
    fake_kisee.post(
        "http://kisee.example.com/jwt/", status=403, body=json.dumps({"_type": "error"})
    )
    with pytest.raises(aiohttp.web_exceptions.HTTPForbidden):
        run(provider.authenticate_user({"login": "toto", "password": "toto"}))


def test_kisee_idp_service_failure(provider, fake_kisee):
    fake_kisee.post(
        "http://kisee.example.com/jwt/", status=500, body=json.dumps({"_type": "error"})
    )
    with pytest.raises(aiohttp.web_exceptions.HTTPBadGateway):
        run(provider.authenticate_user({"login": "toto", "password": "toto"}))
