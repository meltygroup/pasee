import os
import json

import pytest
import asynctest
import sqlite3
from aioresponses import aioresponses

from pasee.pasee import identification_app
from tests import mocks


@pytest.fixture(scope="module")
def db():
    connection = sqlite3.connect(":memory:")
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
        ), (
            "kisee-restrictedguy"
        ), (
            "kisee-guytoadd"
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

    cursor.execute(
        """
        INSERT INTO groups (
            name
        ) VALUES (
            'get_group'
        ), (
            'get_group.staff'
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO user_in_group (
            user, group_name
        ) VALUES (
            'kisee-toto', 'get_group.staff'
        ), (
            'kisee-toto', 'get_group'
        )
        """
    )

    connection.commit()
    cursor.close()
    connection.close()
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
    "identity_providers.kisee.KiseeIdentityProvider._decode_token",
    mocks.decode_token
)
async def test_post_tokens(client):
    with aioresponses(passthrough=["http://127.0.0.1:",]) as mocked:

        mocked.post("http://dump-kisee-endpoint/jwt/", status=201, body=json.dumps({
            "_type": "document",
            "_meta": {"url": "/jwt/", "title": "JSON Web Tokens"},
            "tokens": [
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJleGFtcGxlLmNvbSIsInN1YiI6InRvdG8iLCJleHAiOjE1MzQxNzM3MjMsImp0aSI6ImoyQ01SZVhTVXdjbnZQZmhxcTdjU2cifQ.Gy_ooIE-Bx85elJWXcRmZEtOT4Bbqg3TqSu23F3cHVWrhihm_kwTG1ICVXSGxLkl1AJR1QIwcvosA70CZSnOaQ"
            ],
            "add_token": {
                "_type": "link",
                "action": "post",
                "title": "Create a new JWT",
                "description": "POSTing to this endpoint create JWT tokens.",
                "fields": [
                    {"name": "login", "required": True},
                    {"name": "password", "required": True},
                ],
            },
        }))

        response = await client.post(
            "/tokens/",
            json={
                "data": {
                    "login": "toto@localhost.com",
                    "password": "toto",
                },
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


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_get_groups(client):
    response = await client.get("/groups/")
    assert response.status == 200


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_post_groups(client):
    response = await client.post(
        "/groups/",
        json={"group": "my_group"},
        headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 201

    response = await client.post(
        "/groups/",
        json={},
        headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 422


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization__non_staff,
)
async def test_post_groups__non_staff(client):
    response = await client.post(
        "/groups/",
        json={"group": "my_group"},
        headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 403


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_get_group(client):
    response = await client.get(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 200

    response = await client.get(
        "/groups/group_does_not_exists/",
        headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 404


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization__non_staff,
)
async def test_get_group__raises_not_authorized(client):
    response = await client.get(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 403


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_post_group__success(client):
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"member": "kisee-guytoadd"}
    )
    assert  response.status == 201


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_post_group__raises_not_found_group(client):
    response = await client.post(
        "/groups/unknown_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"member": "kisee-guytoadd"}
    )
    assert response.status == 404


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_post_group__raises_not_found_user(client):
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"member": "kisee-guytoadd-unknown"}
    )
    assert response.status == 404


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization,
)
async def test_post_group__raises_unprocessable_entity(client):
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"wrong-member-fieldname": "kisee-guytoadd"}
    )
    assert  response.status == 422


@asynctest.patch(
    "pasee.middlewares.is_claim_user_authorization",
    mocks.is_claim_user_authorization__non_staff,
)
async def test_post_group__raises_not_authorized(client):
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"member": "kisee-guytoadd"}
    )
    assert  response.status == 403

