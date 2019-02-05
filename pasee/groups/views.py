"""Views for groups ressource in Pasee server, implementing:
"""

import logging
from typing import List

import coreapi
from aiohttp import web

from pasee import utils
from pasee.serializers import serialize
from pasee.groups.utils import (
    is_authorized_for_group,
    is_authorized_for_group_create,
    is_root,
)
from pasee import Unauthorized

logger = logging.getLogger(__name__)


async def get_groups(request: web.Request) -> web.Response:
    """Handlers for GET /groups/
    """
    hostname = request.app.settings["hostname"]
    groups: List = []

    try:
        claims = utils.enforce_authorization(request.headers, request.app.settings)
        if is_root(claims["groups"]):
            user = request.rel_url.query.get("user")
            last_element = request.rel_url.query.get("last_element", "")
            if not user:
                groups = await request.app.storage_backend.get_groups(last_element)
            else:
                groups = await request.app.storage_backend.get_groups_of_user(
                    user, last_element
                )
    except Unauthorized:
        pass
    content = {
        "groups": [
            coreapi.Document(url=f"{hostname}/groups/{group}/", content={"name": group})
            for group in groups
        ],
        "create_group": coreapi.Link(
            action="post",
            title="Create a group",
            description="A method to create a group by a staff member",
            fields=[coreapi.Field(name="group", required=True)],
        ),
        "get_groups_of_user": coreapi.Link(
            action="get",
            title="Get groups of user",
            description="Get list of groups of a user",
            url=f"{hostname}/groups/{{?user}}",
        ),
    }
    if groups:
        content["next"] = coreapi.Link(
            url=f"{hostname}/groups/?last_element={groups[-1]}"
        )
    return serialize(
        request,
        coreapi.Document(
            url=f"{hostname}/groups/",
            title="Groups of Identity Manager",
            content=content,
        ),
    )


async def post_groups(request: web.Request) -> web.Response:
    """Handler for POST /groups/
    """
    claims = utils.enforce_authorization(request.headers, request.app.settings)
    input_data = await request.json()
    if "group" not in input_data:
        raise web.HTTPBadRequest(reason="Missing group")

    group_name = input_data["group"]

    if not is_authorized_for_group_create(claims["groups"], group_name):
        raise web.HTTPForbidden(reason="Not authorized to create group")

    storage_backend = request.app.storage_backend
    staff_group_name = f"{group_name}.staff"

    if await storage_backend.group_exists(group_name):
        raise web.HTTPConflict(reason="Group already exists")

    await storage_backend.create_group(group_name)
    await storage_backend.create_group(staff_group_name)
    await storage_backend.add_member_to_group(claims["sub"], staff_group_name)

    location = f"/groups/{group_name}/"
    return web.Response(status=201, headers={"Location": location})


async def get_group(request: web.Request) -> web.Response:
    """Handler for GET /groups/{group_uid}
    """
    hostname = request.app.settings["hostname"]
    claims = utils.enforce_authorization(request.headers, request.app.settings)
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
            url=f"{hostname}/groups/{{group}}/",
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
    claims = utils.enforce_authorization(request.headers, request.app.settings)
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
    if await storage_backend.is_user_in_group(member, group):
        raise web.HTTPBadRequest(reason="User already in group")

    await storage_backend.add_member_to_group(member, group)
    return web.Response(status=201)


async def delete_group(request: web.Request) -> web.Response:
    """Handler for POST /groups/{group_id}/
    add a user to {group_id}
    """
    claims = utils.enforce_authorization(request.headers, request.app.settings)
    storage_backend = request.app.storage_backend
    group = request.match_info["group_uid"]

    if not is_authorized_for_group(claims["groups"], "staff"):
        raise web.HTTPForbidden(reason="Not authorized to manage group")

    if not await storage_backend.group_exists(group):
        raise web.HTTPNotFound(reason="Group does not exist")

    await storage_backend.delete_group(group)
    await storage_backend.delete_group(f"{group}.staff")
    return web.Response(status=204)


async def delete_group_member(request: web.Request) -> web.Response:
    """Delete group member of group
    """
    claims = utils.enforce_authorization(request.headers, request.app.settings)
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
