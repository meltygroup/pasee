from unittest import mock

import pytest
import asynctest

from pasee.pasee import identification_app
from tests import mocks


@pytest.fixture
def client(loop, aiohttp_client):
    app = identification_app(settings_file="tests/test-settings.toml")
    return loop.run_until_complete(aiohttp_client(app))


async def test_get_root(client):
    response = await client.get("/")
    assert response.status == 200


async def test_get_tokens(client):
    response = await client.get("/tokens/")
    assert response.status == 200


@asynctest.patch(
    "pasee.tokens.views.identify_to_kisee",
    asynctest.CoroutineMock(side_effect=mocks.identify_to_kisee),
)
@mock.patch("pasee.tokens.views.decode_token", mocks.decode_token)
async def test_post_tokens(client):
    response = await client.post(
        "/tokens/",
        json={
            "login": "toto@localhost.com",
            "password": "toto",
            "identity_provider": "kisee",
        },
    )
    assert response.status == 201
    response = await client.post(
        "/tokens/",
        json={
            "login": "toto@localhost.com",
            "password": "toto",
        },
    )
    assert response.status == 422


async def test_get_groups(client):
    response = await client.get("/groups/")
    assert response.status == 200
