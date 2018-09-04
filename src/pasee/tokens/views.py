"""Views for tokens ressource in Pasee server, implementing:

- GET /tokens/
- POST /tokens/
"""
import logging

import coreapi
from aiohttp import web
import jwt

from pasee.serializers import serialize
from pasee.identity_providers import backend as identity_providers
from pasee.utils import import_class


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
    input_data = request.data  # type: ignore
    if "identity_provider" not in input_data:
        raise web.HTTPUnprocessableEntity(reason="Missing identity_provider")
    if "data" not in input_data:
        raise web.HTTPUnprocessableEntity(reason="Missing identity provider input data")

    if input_data["identity_provider"] != "kisee":
        raise web.HTTPUnprocessableEntity(reason="Identity provider not implemented")

    identity_provider_path = identity_providers.BACKENDS[
        input_data["identity_provider"]
    ]
    identity_provider_settings = request.app.settings["idps"][
        input_data["identity_provider"]
    ]
    identity_provider = import_class(identity_provider_path)(identity_provider_settings)

    decoded = await identity_provider.authenticate_user(input_data["data"])
    decoded[  # type: ignore
        "sub"
    ] = f"{input_data['identity_provider']}-{decoded['sub']}"
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
