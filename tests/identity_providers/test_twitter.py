from asyncio import run

import pytest
from aiohttp import web

from pasee.identity_providers.twitter import TwitterIdentityProvider
import mocks

CONSUMER_KEY = "consumer-key-example"
CONSUMER_SECRET = "consumer-secret-example"
CALLBACK_URL = "http://myhost.example.com/callback-url/"


@pytest.fixture
def provider():
    return TwitterIdentityProvider(
        {
            "settings": {
                "consumer_key": CONSUMER_KEY,
                "consumer_secret": CONSUMER_SECRET,
                "callback_url": CALLBACK_URL,
            }
        }
    )


def test_name(provider):
    assert provider.get_name() == "twitter"


def test_endpoint_discovery(provider):
    with pytest.raises(web.HTTPNotImplemented):
        assert run(provider.get_endpoint())


def test_authenticate_user_step_one_returns_authorize_url(provider, monkeypatch):
    monkeypatch.setattr(
        "pasee.identity_providers.twitter.TwitterClient.get_request_token",
        mocks.twitter_get_request_token,
    )
    data = run(provider.authenticate_user({}, step=1))
    assert "authorize_url" in data

    monkeypatch.setattr(
        "pasee.identity_providers.twitter.TwitterClient.get_access_token",
        mocks.twitter_get_access_token,
    )
    data = run(
        provider.authenticate_user({"oauth_token": "", "oauth_verifier": ""}, step=2)
    )
    assert "access_token" in data


def test_authenticate_user_wrong_step_input(provider):
    with pytest.raises(ValueError):
        assert run(provider.authenticate_user({}, step=3))
