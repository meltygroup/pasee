from pasee.identity_providers.twitter import TwitterIdentityProvider

import pytest

CONSUMER_KEY = "consumer-key-example"
CONSUMER_SECRET = "consumer-secret-example"
CALLBACK_URL = "http://myhost.example.com/callback-url/"


@pytest.fixture
def provider():
    return TwitterIdentityProvider(
        {
            "consumer_key": CONSUMER_KEY,
            "consumer_secret": CONSUMER_SECRET,
            "callback_url": CALLBACK_URL
        }
    )


def test_name(provider):
    assert provider.get_name() == "twitter"
