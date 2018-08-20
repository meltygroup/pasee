"""Views for groups ressource in Pasee server, implementing:
"""

import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize


logger = logging.getLogger(__name__)


async def get_groups(request: web.Request) -> web.Response:
    """Handlers for GET /groups/
    """
    return serialize(
        request,
        coreapi.Document(
            url="/groups/", title="Groups of Identity Manager", content={"groups": []}
        ),
    )


async def post_groups(request: web.Request) -> web.Response:
    """Handlers for POST /groups/
    """
    if "superusers" not in request.groups:
        raise web.HTTPUnauthorized(reason="restricted_to_superusers")
    if "group" not in request.data:
        raise web.HTTPUnprocessableEntity(reason="Missing group")

    authorization_backend = request.app.authorization_backend
    await authorization_backend.staff_creates_group(request.user, request.data["group"])
    print(await authorization_backend.get_groups())
    return web.Response(body="OK", status=201)
