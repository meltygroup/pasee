import os
from unittest import mock

import pytest
import asynctest
import sqlite3

from pasee.pasee import identification_app
from tests import mocks


@pytest.fixture(scope="module")
def db():
    connection = sqlite3.connect("tmp_test.db")
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            name TEXT PRIMARY KEY
        );
        """
    )
    cursor.execute("CREATE TABLE IF NOT EXISTS groups(name TEXT PRIMARY KEY);")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_in_group(
            id INTEGER PRIMARY KEY,
            user TEXT,
            group_name TEXT
        );
        """
    )

    cursor.execute(
        """
        INSERT INTO users(
            name
        ) VALUES (
            "kisee-toto"
        )
    """
    )
    cursor.execute("INSERT INTO groups(name) VALUES ('staff')")
    cursor.execute(
        """
        INSERT INTO user_in_group(
            user, group_name
        ) VALUES (
            "kisee-toto", "staff"
        )"""
    )
    cursor.close()
    yield
    os.remove("tmp_test.db")


@pytest.fixture
def client(loop, aiohttp_client, db):
    app = identification_app(settings_file="tests/test-settings.toml")
    return loop.run_until_complete(aiohttp_client(app))


async def test_get_root(client):
    response = await client.get("/")
    assert response.status == 200


async def test_get_tokens(client):
    response = await client.get("/tokens/")
    assert response.status == 200


@asynctest.patch(
    "identity_providers.kisee.KiseeIdentityProvider._identify_to_kisee",
    asynctest.CoroutineMock(side_effect=mocks.identify_to_kisee),
)
@mock.patch(
    "identity_providers.kisee.KiseeIdentityProvider._decode_token",
    mocks.decode_token
)
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


@mock.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_get_groups(client):
    response = await client.get("/groups/")
    assert response.status == 200


@mock.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_post_groups(client):
    response = await client.post(
        "/groups/",
        json={"group": "my_group"},
        headers={"Authorization": "Bearer somefaketoken"}
    )
