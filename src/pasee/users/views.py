"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize
from pasee.identity_providers.utils import get_identity_provider_or_raise

logger = logging.getLogger(__name__)


async def get_users(request: web.Request) -> web.Response:
    """Handlers for GET /users/, just describes that a POST is possible.
    """
    return serialize(
        request,
        coreapi.Document(
            url="/users/",
            title="Users management interface",
            content={
                "Kisee self service registration": coreapi.Link(
                    action="post",
                    title="Self service registration for kisee",
                    description="POSTing to this endpoint to create an user in kisee",
                    fields=[
                        coreapi.Field(name="username", required=True),
                        coreapi.Field(name="password", required=True),
                    ],
                    url="/users/?idp=kisee",
                )
            },
        ),
    )


async def post_users(request: web.Request) -> web.Response:
    """Handler for post /users/, use to create a user
    """
    idp_input = request.rel_url.query.get("idp")
    identity_provider = get_identity_provider_or_raise(
        idp_input, request.app.settings["idps"]
    )
    input_data = await request.json()
    idp_username = await identity_provider.register_user(input_data)
    passe_username = f"{idp_input}-{idp_username}"
    await request.app.authorization_backend.create_user(passe_username)

    location = f"/users/{passe_username}/"
    return web.Response(status=201, headers={"Location": location})
