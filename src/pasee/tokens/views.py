"""Views for tokens ressource in Pasee server, implementing:

- GET /tokens/
- POST /tokens/
"""

import json
import logging

import coreapi
import aiohttp
from aiohttp import web
import jwt

from pasee.serializers import serialize


logger = logging.getLogger(__name__)


async def get_tokens(request: web.Request) -> web.Response:
    """Handlers for GET /token/, just describes that a POST is possible.
    """
    return serialize(
        request,
        coreapi.Document(
            url="/token",
            title="Request Token From Identity Provider",
            content={
                "tokens": [],
                "identify_to_identity_provider": coreapi.Link(
                    action="post",
                    title="Request Token From Identity Provider",
                    description="POSTing to this endpoint to request a token",
                    fields=[
                        coreapi.Field(name="login", required=True),
                        coreapi.Field(name="password", required=True),
                        coreapi.Field(name="identity_provider", required=True),
                    ],
                ),
            },
        ),
    )


async def post_token(request: web.Request) -> web.Response:
    """Post to IDP to create a jwt token
    """
    if "login" not in request.data or "password" not in request.data:
        raise web.HTTPUnprocessableEntity(reason="Missing login or password.")
    if "identity_provider" not in request.data:
        raise web.HTTPUnprocessableEntity(reason="Missing identity_provider")

    if request.data["identity_provider"] != "kisee":
        raise web.HTTPUnprocessableEntity(reason="Identity provider not implemented")

    kisee_settings = request.app.settings["idps"]["kisee"]
    kisee_public_keys = kisee_settings["settings"]["public_keys"]
    url = kisee_settings["endpoint"]

    logger.debug("Trying to identify user %s", request.data["login"])
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, headers={"Content-Type": "application/json"}, json=request.data
        ) as response:
            kisee_response = await response.text()
            kisee_response = json.loads(kisee_response)

    # TODO use header location instead to retrieve token
    # kisee_headers = response.headers
    # token_location = kisee_headers["Location"]

    token = kisee_response["tokens"][0]

    decoded = None
    for public_key in kisee_public_keys:
        try:
            decoded = jwt.decode(token, public_key)
        except ValueError:
            pass
    if not decoded:
        raise web.HTTPInternalServerError()

    decoded[  # type: ignore
        "sub"
    ] = f"{request.data['identity_provider']}-{decoded['sub']}"
    decoded[  # type: ignore
        "groups"
    ] = await request.app.authorization_backend.get_authorizations_for_user(
        decoded["sub"]
    )
    encoded = jwt.encode(
        decoded,
        request.app.settings["private_key"],
        algorithm=request.app.settings["algorithm"],
    )

    return serialize(
        request,
        coreapi.Document(
            url="/tokens/",
            title="Create a token with Identify Provider",
            content={
                "tokens": [encoded.decode("utf-8")],
                "identify": coreapi.Link(
                    action="post",
                    title="Identify",
                    description="Identifying to an Identity Provider",
                    fields=[
                        coreapi.Field(name="login", required=True),
                        coreapi.Field(name="password", required=True),
                        coreapi.Field(name="identity_provider", required=True),
                    ],
                ),
            },
        ),
        status=201,
    )
