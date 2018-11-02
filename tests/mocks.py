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


def enforce_authorization(request):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "groups": ["staff", "my_group", "my_group.staff"],
    }


def enforce_authorization_for_refresh_token(request):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "refresh_token": True,
        "groups": ["staff", "my_group", "my_group.staff"],
    }


def enforce_authorization_for_refresh_token_without_claim(request):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "groups": ["staff", "my_group", "my_group.staff"],
    }


def enforce_authorization__non_staff(request):
    return {
        "iss": "example.com",
        "sub": "kisee-toto",
        "exp": 1536221551,
        "jti": "T4FVrRkN3rqeR6wR9Fxf6R",
        "groups": ["non_staff"],
    }
