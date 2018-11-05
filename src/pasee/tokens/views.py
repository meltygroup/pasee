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
from pasee.tokens.handlers import handle_oauth_callback
from pasee import utils, Unauthorized


logger = logging.getLogger(__name__)


async def get_tokens(request: web.Request) -> web.Response:
    """Handlers for GET /token/, just describes that a POST is possible.
    """
    access_token, refresh_token = None, None
    identity_provider_input = request.rel_url.query.get("idp", None)
    if identity_provider_input:
        access_token, refresh_token = await handle_oauth_callback(
            identity_provider_input, request
        )
        access_token = access_token.decode("utf-8")
        refresh_token = refresh_token.decode("utf-8")

    return serialize(
        request,
        coreapi.Document(
            url="/token",
            title="Request Token From Identity Provider",
            content={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "identify_to_kisee": coreapi.Link(
                    action="post",
                    title="Login via login/password pair",
                    description="POSTing to this endpoint will identify you by "
                    "login/password.",
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

    response_content = {
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
        )
    }

    if "sub" in claims:
        storage_backend = request.app.storage_backend
        if not await storage_backend.user_exists(claims["sub"]):
            await storage_backend.create_user(claims["sub"])

        claims["groups"] = await storage_backend.get_authorizations_for_user(
            claims["sub"]
        )
        access_token, refresh_token = generate_access_token_and_refresh_token_pairs(
            claims,
            request.app.settings["private_key"],
            algorithm=request.app.settings["algorithm"],
        )
        response_content["access_token"] = access_token.decode("utf-8")
        response_content["refresh_token"] = refresh_token.decode("utf-8")
    else:
        response_content["authorize_url"] = claims["authorize_url"]

    return serialize(
        request,
        coreapi.Document(
            url="/tokens/",
            title="Create a token with Identify Provider",
            content=response_content,
        ),
        status=201,
    )
