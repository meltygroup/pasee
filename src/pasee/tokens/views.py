"""Views for tokens ressource in Pasee server, implementing:

- GET /tokens/
- POST /tokens/
"""
import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize
from pasee.tokens.handlers import generate_access_token_and_refresh_token_pairs
from pasee.tokens.handlers import generate_claims_with_identity_provider
from pasee import utils


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
                        coreapi.Field(name="data", required=True),
                        coreapi.Field(name="identity_provider", required=True),
                    ],
                ),
            },
        ),
    )


async def post_token(request: web.Request) -> web.Response:
    """Post to IDP to create a jwt token
    """

    # If an Authorization header is available, we proceed it as a refresh token
    try:
        claims = utils.enforce_authorization(request)
        if "refresh_token" not in claims or claims["refresh_token"] is not True:
            raise web.HTTPBadRequest(reason="token_is_not_refresh_token")
    except web.HTTPBadRequest as error:
        if error.text != "400: missing_authorization_header":
            raise error
        claims = {}

    if not claims:
        claims = await generate_claims_with_identity_provider(request)

    access_token, refresh_token = generate_access_token_and_refresh_token_pairs(
        claims,
        request.app.settings["private_key"],
        algorithm=request.app.settings["algorithm"],
    )

    return serialize(
        request,
        coreapi.Document(
            url="/tokens/",
            title="Create a token with Identify Provider",
            content={
                "access_token": access_token.decode("utf-8"),
                "refresh_token": refresh_token.decode("utf-8"),
                "create_tokens": coreapi.Link(
                    action="post",
                    title="Create tokens",
                    description="Requesting access and refresh tokens",
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
