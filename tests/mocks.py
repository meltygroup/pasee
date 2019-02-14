"""Mocks
"""


def identify_to_kisee(self, data):
    return {
        "_type": "document",
        "_meta": {"url": "/jwt/", "title": "JSON Web Tokens"},
        "tokens": ["somefaketoken"],
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


def decode_token(self, token):
    """Decode a token emitted by Kisee
    """
    return {
        "iss": "example.com",
        "sub": "toto",
        "exp": 1534173723,
        "jti": "j2CMReXSUwcnvPfhqq7cSg",
    }


def decode_token__new_user(self, token):
    """Decode a token emitted by Kisee
    with a user who does not exist in database
    """
    return {
        "iss": "example.com",
        "sub": "newguy",
        "exp": 1534173723,
        "jti": "j2CMReXSUwcnvPfhqq7cSg",
    }


def enforce_authorization(headers, settings):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "groups": ["staff", "my_group", "my_group.staff"],
    }


def enforce_authorization_for_refresh_token(headers, settings):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "refresh_token": True,
        "groups": ["staff", "my_group", "my_group.staff"],
    }


def enforce_authorization_for_refresh_token_without_claim(headers, settings):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "groups": ["staff", "my_group", "my_group.staff"],
    }


def enforce_authorization__non_staff(headers, settings):
    return {
        "iss": "example.com",
        "sub": "kisee-tototo",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "groups": ["non_staff"],
    }


async def twitter__authenticate_user(self, data, step=1):
    if step == 1:
        return {"authorize_url": "http://some-authorize-url.example.com"}
    elif step == 2:
        return {"access_token": "random-access-token", "sub": "newtwitteruser"}
    raise ValueError("Step should be either 1 or 2")


async def twitter__authenticate_user__user_exists(self, data, step=1):
    if step == 1:
        return {"authorize_url": "http://some-authorize-url.example.com"}
    elif step == 2:
        return {"access_token": "random-access-token", "sub": "foo"}
    raise ValueError("Step should be either 1 or 2")


async def twitter_get_request_token(self, loop=None, **params):
    self.oauth_token = "oauth_token_example"
    self.oauth_token_secret = "oauth_token_secret_example"
    return self.oauth_token, self.oauth_token_secret, {}


async def twitter_get_access_token(
    self, oauth_verifier, request_token=None, loop=None, **params
):
    return (
        "access_token_example",
        "access_token_secret_example",
        {"user_id": "sub_example"},
    )


def join(path, *paths):
    return "tests/test-settings.toml"
