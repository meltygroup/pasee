"""Mocks
"""


def identify_to_kisee(self, data):
    return {
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


def decode_token(self, token):
    return {
        "iss": "example.com",
        "sub": "toto",
        "exp": 1534173723,
        "jti": "j2CMReXSUwcnvPfhqq7cSg",
    }


def enforce_authorization(request):
    return "kisee-toto", ["my_group", "my_group.staff", "staff"]


def enforce_authorization__non_staff(request):
    return "kisee-toto", ["non-staff"]
