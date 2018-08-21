"""Views for groups ressource in Pasee server, implementing:
"""

import logging
import json

import coreapi
from aiohttp import web

from pasee.serializers import serialize


logger = logging.getLogger(__name__)


async def get_groups(request: web.Request) -> web.Response:
    """Handlers for GET /groups/
    """
    authorization_backend = request.app.authorization_backend
    groups = await authorization_backend.get_groups()
    return serialize(
        request,
        coreapi.Document(
            url="/groups/",
            title="Groups of Identity Manager",
            content={
                "groups": groups,
                "create_group": coreapi.Link(
                    action="post",
                    title="Create a group",
                    description="A method to create a group by a staff member",
                    fields=[coreapi.Field(name="group", required=True)],
                ),
            },
        ),
    )


async def post_groups(request: web.Request) -> web.Response:
    """Handlers for POST /groups/
    """
    if "group" not in request.data:
        raise web.HTTPUnprocessableEntity(reason="Missing group")

    group_name = request.data["group"]
    group_name_splited = group_name.rsplit(".", 1)
    group_name_root_staff = (
        (group_name_splited[0] + ".staff") if len(group_name_splited) > 2 else "staff"
    )
    print(group_name_root_staff)

    if group_name_root_staff not in request.groups:
        raise web.HTTPUnauthorized(reason="restricted_to_staff")

    authorization_backend = request.app.authorization_backend
    await authorization_backend.staff_creates_group(request.user, group_name)
    location = f"/groups/{group_name}/"
    print(await authorization_backend.get_groups())
    return web.Response(status=201, headers={"Location": location})


async def get_group(request: web.Request) -> web.Response:
    """Handlers for GET /groups/{group_uid}
    """
    authorization_backend = request.app.authorization_backend
    group = request.match_info["group_uid"]
    if not await authorization_backend.group_exists(group):
        return web.HTTPNotFound(reason="group_does_not_exist")
    members = await authorization_backend.get_members_of_group(group)
    response = {"members": members}
    return web.Response(status=200, body=json.dumps(response))
