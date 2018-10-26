"""Views for groups ressource in Pasee server, implementing:
"""

import logging

import coreapi
from aiohttp import web

from pasee import utils
from pasee.serializers import serialize
from pasee.groups.utils import is_authorized_for_group

logger = logging.getLogger(__name__)


async def get_groups(request: web.Request) -> web.Response:
    """Handlers for GET /groups/
    """
    utils.enforce_authorization(request)
    storage_backend = request.app.storage_backend
    groups = await storage_backend.get_groups()
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
    """Handler for POST /groups/
    """
    claims = utils.enforce_authorization(request)
    input_data = await request.json()
    if "group" not in input_data:
        raise web.HTTPBadRequest(reason="Missing group")

    group_name = input_data["group"]
    group_name_splited = group_name.rsplit(".", 1)
    group_name_root_staff = (
        (group_name_splited[0] + ".staff") if len(group_name_splited) > 2 else "staff"
    )

    if group_name_root_staff not in claims["groups"]:
        raise web.HTTPForbidden(reason="Restricted to staff")

    storage_backend = request.app.storage_backend
    staff_group_name = f"{group_name}.staff"

    if await storage_backend.group_exists(group_name):
        raise web.HTTPConflict(reason="Group already exists")

    await storage_backend.create_group(group_name)
    await storage_backend.create_group(staff_group_name)
    await storage_backend.add_member_to_group(claims["sub"], group_name)
    await storage_backend.add_member_to_group(claims["sub"], staff_group_name)

    location = f"/groups/{group_name}/"
    return web.Response(status=201, headers={"Location": location})


async def get_group(request: web.Request) -> web.Response:
    """Handler for GET /groups/{group_uid}
    """
    claims = utils.enforce_authorization(request)
    storage_backend = request.app.storage_backend
    group = request.match_info["group_uid"]

    if not is_authorized_for_group(claims["groups"], group):
        raise web.HTTPForbidden(reason="Not authorized to view group")

    if not await storage_backend.group_exists(group):
        raise web.HTTPNotFound(reason="Group does not exist")

    members = await storage_backend.get_members_of_group(group)
    return serialize(
        request,
        coreapi.Document(
            url=f"/groups/{group}/",
            title=f"{group} group management interface",
            content={
                "members": members,
                "add_member": coreapi.Link(
                    action="post",
                    title="Add a member to group",
                    description="A method to add a member to group",
                    fields=[coreapi.Field(name="member", required=True)],
                ),
            },
        ),
    )


async def post_group(request: web.Request) -> web.Response:
    """Handler for POST /groups/{group_id}/
    add a user to {group_id}
    """
    claims = utils.enforce_authorization(request)
    input_data = await request.json()
    storage_backend = request.app.storage_backend
    group = request.match_info["group_uid"]

    if not is_authorized_for_group(claims["groups"], group):
        raise web.HTTPForbidden(reason="Not authorized to manage group")

    if not await storage_backend.group_exists(group):
        raise web.HTTPNotFound(reason="Group does not exist")

    if "member" not in input_data:
        raise web.HTTPBadRequest(reason="Missing member in request body")
    member = input_data["member"]
    if not await storage_backend.user_exists(member):
        raise web.HTTPNotFound(reason="Member to add does not exist")

    await storage_backend.add_member_to_group(member, group)
    return web.Response(status=201)


async def delete_group_member(request: web.Request) -> web.Response:
    """Delete group member of group
    """
    claims = utils.enforce_authorization(request)
    storage_backend = request.app.storage_backend
    group = request.match_info["group_uid"]
    member = request.match_info["member_uid"]

    if not await storage_backend.group_exists(group):
        raise web.HTTPNotFound(reason="Group does not exist")
    if not is_authorized_for_group(claims["groups"], group):
        raise web.HTTPForbidden(reason="Not authorized to manage group")
    if not await storage_backend.is_user_in_group(member, group):
        raise web.HTTPNotFound(reason="User does not exist in group")
    await storage_backend.delete_member_in_group(member, group)
    return web.Response(status=204)
