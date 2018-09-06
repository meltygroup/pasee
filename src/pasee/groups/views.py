"""Views for groups ressource in Pasee server, implementing:
"""

import logging
from typing import List

import coreapi
from aiohttp import web

from pasee import utils
from pasee.serializers import serialize

logger = logging.getLogger(__name__)


def is_authorized(authorized_group: str, groups: List[str]) -> bool:
    """Check if authorized group is in user group collection
    Written as a standalone function for easy mocking in pytest
    """
    return authorized_group in groups


async def get_groups(request: web.Request) -> web.Response:
    """Handlers for GET /groups/
    """
    utils.enforce_authorization(request)
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
        raise web.HTTPForbidden(reason="restricted_to_staff")

    authorization_backend = request.app.authorization_backend
    staff_group_name = f"{group_name}.staff"
    await authorization_backend.create_group(group_name)
    await authorization_backend.create_group(staff_group_name)
    await authorization_backend.add_member_to_group(claims["sub"], group_name)
    await authorization_backend.add_member_to_group(claims["sub"], staff_group_name)

    location = f"/groups/{group_name}/"
    return web.Response(status=201, headers={"Location": location})


async def get_group(request: web.Request) -> web.Response:
    """Handler for GET /groups/{group_uid}
    """
    claims = utils.enforce_authorization(request)
    authorization_backend = request.app.authorization_backend
    group = request.match_info["group_uid"]

    if not await authorization_backend.group_exists(group):
        raise web.HTTPNotFound(reason="group_does_not_exist")

    if is_authorized("staff", claims["groups"]) or is_authorized(
        group, claims["groups"]
    ):
        members = await authorization_backend.get_members_of_group(group)
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

    raise web.HTTPForbidden(reason="not_authorized_to_view_members")


async def post_group(request: web.Request) -> web.Response:
    """Handler for POST /groups/{group_id}/
    add a user to {group_id}
    """
    claims = utils.enforce_authorization(request)
    input_data = await request.json()
    authorization_backend = request.app.authorization_backend
    group = request.match_info["group_uid"]

    if not await authorization_backend.group_exists(group):
        raise web.HTTPNotFound(reason="group_does_not_exist")

    if "member" not in input_data:
        raise web.HTTPBadRequest(reason="missing_member_in_request_body")
    member = input_data["member"]
    if not await authorization_backend.user_exists(member):
        raise web.HTTPNotFound(reason="member_to_add_does_not_exist")
    if is_authorized("staff", claims["groups"]) or is_authorized(
        f"{group}.staff", claims["groups"]
    ):
        await authorization_backend.add_member_to_group(member, group)
        return web.Response(status=201)
    raise web.HTTPForbidden(reason="not_authorized_to_add_member")
