"""Views for tokens ressource in Pasee server, implementing:

- GET /tokens/
- POST /tokens/
"""
import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize
from pasee.tokens.handlers import generate_access_token_and_refresh_token_pairs
from pasee.tokens.handlers import authenticate_with_identity_provider
from pasee.tokens.handlers import retrieve_authorizations_create_user_if_not_exist
from pasee import utils, Unauthorized


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
                "identify_to_kisee": coreapi.Link(
                    action="post",
                    title="Login via login/password pair",
                    description="""
                        POSTing to this endpoint will identify you by login/password.
                    """,
                    fields=[
                        coreapi.Field(name="login", required=True),
                        coreapi.Field(name="password", required=True),
                    ],
                    url="/tokens/?idp=kisee",
                ),
            },
        ),
    )


async def post_token(request: web.Request) -> web.Response:
    """Post to IDP to create a jwt token
    """
    # Proceed as a refresh token handler if query string refresh is available
    if "refresh" in request.rel_url.query:
        if not request.headers.get("Authorization"):
            raise web.HTTPBadRequest(
                reason="Missing Authorization header for refreshing access token"
            )
        claims = utils.enforce_authorization(request)
        if not claims.get("refresh_token", False):
            raise Unauthorized("Token is not a refresh token")
    else:
        claims = await authenticate_with_identity_provider(request)
        await retrieve_authorizations_create_user_if_not_exist(
            request.app.authorization_backend, claims
        )

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
                "identify_to_kisee": coreapi.Link(
                    action="post",
                    title="Login via login/password pair",
                    description="""
                        POSTing to this endpoint will identify you by login/password.
                    """,
                    fields=[
                        coreapi.Field(name="login", required=True),
                        coreapi.Field(name="password", required=True),
                    ],
                    url="/tokens/?idp=kisee",
                ),
            },
        ),
        status=201,
    )
