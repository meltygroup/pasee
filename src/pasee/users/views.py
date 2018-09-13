"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize
from pasee.identity_providers.utils import get_identity_provider_with_capability
from pasee.exceptions import UserAlreadyExist

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
                    url="/users/",
                )
            },
        ),
    )


async def post_users(request: web.Request) -> web.Response:
    """Handler for post /users/, use to create a user
    """
    identity_provider = get_identity_provider_with_capability(
        request.app.settings["idps"], "register"
    )

    input_data = await request.json()
    if not all(key in input_data.keys() for key in {"username", "password"}):
        raise web.HTTPBadRequest(
            reason=f"Missing required fields for {identity_provider}.get_name()"
        )

    idp_username = input_data["username"]
    passe_username = f"{identity_provider.get_name()}-{idp_username}"

    if await request.app.authorization_backend.user_exists(passe_username):
        raise web.HTTPBadRequest(reason="User already exist in pasee database")

    try:
        await identity_provider.register_user(input_data)
    except UserAlreadyExist:
        raise web.HTTPConflict(
            reason=f"User already exist in {identity_provider.get_name()}"
        )

    await request.app.authorization_backend.create_user(passe_username)

    location = f"/users/{passe_username}/"
    return web.Response(status=201, headers={"Location": location})
