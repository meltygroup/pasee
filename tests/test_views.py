import json

import pytest
from aioresponses import aioresponses

from pasee.pasee import identification_app
import mocks


async def load_fake_data(app):
    conn = app.storage_backend.connection
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                name TEXT PRIMARY KEY,
                is_banned BOOLEAN DEFAULT FALSE
            );
            """
        )
        conn.execute("CREATE TABLE IF NOT EXISTS groups(name TEXT PRIMARY KEY);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_in_group(
                id INTEGER PRIMARY KEY,
                user TEXT,
                group_name TEXT
            );
            """
        )

        conn.execute(
            """
            INSERT INTO users(
                name
            ) VALUES (
                "kisee-toto"
            ), (
                "kisee-restrictedguy"
            ), (
                "kisee-guytoadd"
            ), (
                "kisee-guytodel"
            ), (
                "twitter-foo"
            ), (
                "kisee-deleteme"
            ), (
                "kisee-banme"
            )
            """
        )

        conn.execute("INSERT INTO groups(name) VALUES ('staff')")
        conn.execute(
            """
            INSERT INTO user_in_group(
                user, group_name
            ) VALUES (
                "kisee-toto", "staff"
            )"""
        )

        conn.execute(
            """
            INSERT INTO groups (
                name
            ) VALUES (
                'get_group'
            ), (
                'get_group.staff'
            ), (
                'group_to_delete'
            ), (
                'group_to_delete.staff'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO user_in_group (
                user, group_name
            ) VALUES (
                'kisee-toto', 'get_group.staff'
            ), (
                'kisee-toto', 'get_group'
            ), (
                'kisee-guytodel', 'get_group'
            )
            """
        )


@pytest.fixture
def client(loop, aiohttp_client):
    app = identification_app(settings_file="tests/test-settings.toml")
    app.on_startup.append(load_fake_data)
    return loop.run_until_complete(aiohttp_client(app))


async def test_get_root(client):
    response = await client.get("/")
    assert response.status == 200


async def test_get_public_key(client):
    response = await client.get("/public-key/")
    assert response.status == 200


async def test_get_tokens(client):
    response = await client.get("/tokens/")
    assert response.status == 200


async def test_post_tokens__twitter(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.identity_providers.twitter.TwitterIdentityProvider.authenticate_user",
        mocks.twitter__authenticate_user,
    )
    response = await client.post("/tokens/?idp=twitter")
    assert response.status == 201


async def test_get_tokens__twitter_callback(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.identity_providers.twitter.TwitterIdentityProvider.authenticate_user",
        mocks.twitter__authenticate_user,
    )
    response = await client.get(
        "/tokens/?idp=twitter&oauth_verifier=some_random_token&oauth_token=some_random_token",
        json={"login": "test"},
    )
    assert response.status == 200


async def test_get_tokens__twitter_callback__user_exists(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.identity_providers.twitter.TwitterIdentityProvider.authenticate_user",
        mocks.twitter__authenticate_user__user_exists,
    )
    response = await client.get(
        "/tokens/?idp=twitter&oauth_verifier=some_random_token&oauth_token=some_random_token",
        json={"login": "test"},
    )
    assert response.status == 200


async def test_get_tokens__oauth_unknown_idp(client):
    response = await client.get(
        "/tokens/?idp=unknown&oauth_verifier=some_random_token&oauth_token=some_random_token",
        json={"login": "test"},
    )
    assert response.status == 400


async def test_post_tokens(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.identity_providers.kisee.KiseeIdentityProvider._decode_token",
        mocks.decode_token,
    )
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:

        mocked.post(
            "http://dump-kisee-endpoint/jwt/",
            status=201,
            body=json.dumps(
                {
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
                }
            ),
        )

        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "http://dump-kisee-endpoint/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "http://dump-kisee-endpoint/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )

        response = await client.post(
            "/tokens/?idp=kisee",
            json={"login": "toto@localhost.com", "password": "toto"},
        )
        assert response.status == 201


async def test_post_tokens__kisee_not_available(client):
    response = await client.post(
        "/tokens/?idp=kisee", json={"login": "toto@localhost.com", "password": "toto"}
    )
    assert response.status == 503


async def test_post_tokens__creates_new_user(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.identity_providers.kisee.KiseeIdentityProvider._decode_token",
        mocks.decode_token__new_user,
    )
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:

        mocked.post(
            "http://dump-kisee-endpoint/jwt/",
            status=201,
            body=json.dumps(
                {
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
                }
            ),
        )

        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "http://dump-kisee-endpoint/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "http://dump-kisee-endpoint/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )

        response = await client.post(
            "/tokens/?idp=kisee",
            json={"login": "toto@localhost.com", "password": "toto"},
        )
        assert response.status == 201


async def test_post_tokens__missing_idp_query_string(client, monkeypatch):
    response = await client.post(
        "/tokens/", json={"login": "toto@localhost.com", "password": "toto"}
    )
    assert response.status == 400


async def test_post_tokens__idp_not_implemented(client, monkeypatch):
    response = await client.post(
        "/tokens/?idp=not_implemented",
        json={"login": "toto@localhost.com", "password": "toto"},
    )
    assert response.status == 400


async def test_get_users(client):
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )

        response = await client.get("/users/")
        assert response.status == 200


async def test_get_users__corrupted_authorization_header(client, monkeypatch):
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )

        response = await client.get(
            "/users/", headers={"Authorization": "not-event-bearer"}
        )
        assert response.status == 200


async def test_get_users__as_staff(client, monkeypatch):
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )
        monkeypatch.setattr(
            "pasee.utils.enforce_authorization", mocks.enforce_authorization
        )

        response = await client.get(
            "/users/", headers={"Authorization": "Bearer somefaketoken"}
        )
        assert response.status == 200


async def test_get_users__as_staff_with_after_query_string(client, monkeypatch):
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )
        monkeypatch.setattr(
            "pasee.utils.enforce_authorization", mocks.enforce_authorization
        )

        response = await client.get(
            "/users/?after=kisee-42", headers={"Authorization": "Bearer somefaketoken"}
        )
        assert response.status == 200


async def test_get_users__as_staff_with_random_query_string(client, monkeypatch):
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )
        monkeypatch.setattr(
            "pasee.utils.enforce_authorization", mocks.enforce_authorization
        )

        response = await client.get(
            "/users/?random-param=random-value",
            headers={"Authorization": "Bearer somefaketoken"},
        )
        assert response.status == 200


async def test_get_users__as_non_staff(client, monkeypatch):
    with aioresponses(passthrough=["http://127.0.0.1:"]) as mocked:
        mocked.get(
            "http://dump-kisee-endpoint/",
            status=200,
            body=json.dumps(
                {
                    "resources": {
                        "jwt": {
                            "hints": {
                                "allow": ["GET", "POST"],
                                "formats": {"application/coreapi+json": {}},
                            },
                            "href": "/jwt/",
                        }
                    },
                    "actions": {
                        "register-user": {
                            "fields": [
                                {"name": "username", "required": True},
                                {"required": True, "name": "password"},
                                {"name": "email", "required": True},
                            ],
                            "href": "/users/",
                            "method": "POST",
                        },
                        "create-token": {
                            "method": "POST",
                            "href": "/jwt/",
                            "fields": [
                                {"name": "login", "required": True},
                                {"name": "password", "required": True},
                            ],
                        },
                    },
                    "api": {
                        "links": {
                            "describedBy": "https://doc.meltylab.fr",
                            "author": "mailto:julien@palard.fr",
                        },
                        "title": "Identification Provider",
                    },
                }
            ),
        )
        monkeypatch.setattr(
            "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
        )

        response = await client.get(
            "/users/", headers={"Authorization": "Bearer somefaketoken"}
        )
        assert response.status == 200


async def test_get_user(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.get(
        "/users/kisee-toto", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 200


async def test_get_user__no_groups(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.get(
        "/users/kisee-restrictedguy", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 200


async def test_get_user__user_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.get(
        "/users/kisee-hedoesnotexist", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 404


async def test_get_user__not_authorized(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.get(
        "/users/kisee-toto", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 403


async def test_patch_user(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.patch(
        "/users/kisee-banme",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"is_banned": True},
    )
    assert response.status == 204


async def test_patch_user__no_valid_field_to_patch(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.patch(
        "/users/kisee-banme",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"not_valid": True},
    )
    assert response.status == 204


async def test_patch_user__bad_request(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.patch(
        "/users/kisee-banme",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"username": "kisee-banme2"},
    )
    assert response.status == 400


async def test_patch_user__not_found(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.patch(
        "/users/kisee-userdoestnotexist",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"is_banned": True},
    )
    assert response.status == 404


async def test_patch_user__not_authorized(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.patch(
        "/users/kisee-banme",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"is_banned": True},
    )
    assert response.status == 403


async def test_delete_user__non_staff(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.delete(
        "/users/kisee-deleteme", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 403


async def test_delete_user(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.delete(
        "/users/kisee-deleteme", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 204


async def test_post_tokens__refresh_token(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization",
        mocks.enforce_authorization_for_refresh_token,
    )
    response = await client.post(
        "/tokens/?refresh", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 201


async def test_post_tokens__refresh_token__unauthorized(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization",
        mocks.enforce_authorization_for_refresh_token_without_claim,
    )
    response = await client.post(
        "/tokens/?refresh", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 400


async def test_post_tokens__refresh_token__missing_header(client, monkeypatch):
    response = await client.post("/tokens/?refresh")
    assert response.status == 400


async def test_get_groups(client):
    response = await client.get("/groups/")
    assert response.status == 200


async def test_get_groups__with_corrupted_authorization_header(client):
    response = await client.get(
        "/groups/", headers={"Authorization": "not-event-bearer-token"}
    )
    assert response.status == 200


async def test_get_groups__with_authorization_header(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.get(
        "/groups/", headers={"Authorization": "Bearer faketoken"}
    )
    assert response.status == 200


async def test_get_groups__with_authorization_header_non_staff(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.get(
        "/groups/", headers={"Authorization": "Bearer faketoken"}
    )
    assert response.status == 200


async def test_get_groups__of_user(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.get(
        "/groups/?user=kisee-toto", headers={"Authorization": "Bearer faketoken"}
    )
    assert response.status == 200


async def test_post_groups(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/",
        json={"group": "my_group"},
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 201

    response = await client.post(
        "/groups/", json={}, headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 400


async def test_post_groups__parent_staff(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/",
        json={"group": "my_group.somegroup"},
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 201


async def test_post_groups__non_parent_staff(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/",
        json={"group": "group_i_dont_belong.new_sub_group"},
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 201


async def test_post_groups__conflict(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/",
        json={"group": "get_group"},
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 409


async def test_post_groups__non_staff(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.post(
        "/groups/",
        json={"group": "my_group"},
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 403


async def test_get_group(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.get(
        "/groups/get_group/", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 200

    response = await client.get(
        "/groups/group_does_not_exists/",
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 404


async def test_get_group__raises_not_authorized(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.get(
        "/groups/get_group/", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 403


async def test_delete_group__forbidden(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.delete(
        "/groups/group_to_delete/", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 403


async def test_delete_group__not_found(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.delete(
        "/groups/group_not_exist/", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 404


async def test_delete_group(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.delete(
        "/groups/group_to_delete/", headers={"Authorization": "Bearer somefaketoken"}
    )
    assert response.status == 204


async def test_delete_group_member(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.delete(
        "/groups/get_group/kisee-guytodel/",
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 204


async def test_delete_group_member__http_not_found__group(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.delete(
        "/groups/group_does_not_exist/kisee-guytodel/",
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 404


async def test_delete_group_member__http_not_found__user(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.delete(
        "/groups/get_group/user-does-not-exist/",
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 404


async def test_delete_group_member__http_not_authorized(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.delete(
        "/groups/get_group/user-does-not-exist/",
        headers={"Authorization": "Bearer somefaketoken"},
    )
    assert response.status == 403


async def test_post_group__success(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"username": "kisee-guytoadd"},
    )
    assert response.status == 201


async def test_post_group__raises_not_found_group(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/unknown_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"username": "kisee-guytoadd"},
    )
    assert response.status == 404


async def test_post_group__user_does_not_exist(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"username": "kisee-guytoadd-unknown"},
    )
    assert response.status == 201


async def test_post_group__raises_user_already_in_group(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"username": "kisee-toto"},
    )
    assert response.status == 400


async def test_post_group__raises_unprocessable_entity(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization
    )
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"wrong-member-fieldname": "kisee-guytoadd"},
    )
    assert response.status == 400


async def test_post_group__raises_not_authorized(client, monkeypatch):
    monkeypatch.setattr(
        "pasee.utils.enforce_authorization", mocks.enforce_authorization__non_staff
    )
    response = await client.post(
        "/groups/get_group/",
        headers={"Authorization": "Bearer somefaketoken"},
        json={"username": "kisee-guytoadd"},
    )
    assert response.status == 403
