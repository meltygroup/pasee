"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import logging
from typing import List
from urllib.parse import parse_qs

import coreapi
from aiohttp import web

from pasee import Unauthorized, Unauthenticated
from pasee.serializers import serialize
from pasee.identity_providers.utils import get_identity_provider_with_capability
from pasee.groups.utils import is_root
from pasee import utils

logger = logging.getLogger(__name__)


async def get_users(request: web.Request) -> web.Response:
    """Handlers for GET /users/, just describes that a POST is possible.
    """
    hostname = request.app.settings["hostname"]
    identity_provider = get_identity_provider_with_capability(
        request.app.settings, "register-user"
    )
    register_user_endpoint = await identity_provider.get_endpoint("register-user")

    users: List[str] = []
    errors: List[coreapi.Error] = []
    last_element = None
    try:
        claims = utils.enforce_authorization(request.headers, request.app.settings)
        if is_root(claims["groups"]):
            after = request.rel_url.query.get("after", "")
            users = await request.app.storage_backend.get_users(after)
            last_element = users[-1] if users else None

    except Unauthorized as unauthorized_error:
        errors.append(coreapi.Error(content={"reason": unauthorized_error.reason}))
    except Unauthenticated:
        pass

    content = {
        "users": [
            coreapi.Document(url=f"{hostname}/groups/{user}/", content={"user": user})
            for user in users
        ],
        "Self service registration": coreapi.Link(
            action="get",
            title="Self service registration for identity provider",
            description="Get more information on how to self register",
            url=register_user_endpoint,
        ),
        "errors": errors,
    }

    if last_element:
        if request.rel_url.query:
            if not request.rel_url.query.get("after"):
                next_endpoint = f"{hostname}{request.rel_url}&after={last_element}"
            else:
                parsed_query = parse_qs(request.rel_url.raw_query_string)
                query = {key: "".join(value) for key, value in parsed_query.items()}
                query["after"] = last_element
                query_string = "?" + "&".join(
                    [f"{key}={value}" for key, value in query.items()]
                )
                next_endpoint = f"{hostname}{request.path}{query_string}"
        else:
            next_endpoint = f"{hostname}{request.rel_url}?after={last_element}"
        content["next"] = coreapi.Link(url=next_endpoint)

    return serialize(
        request,
        coreapi.Document(
            url=f"{hostname}/users/",
            title="Users management interface",
            content=content,
        ),
    )


async def get_user(request: web.Request) -> web.Response:
    """Handlers for GET /users/{user-uid}
    List groups of {user-uid}
    """
    hostname = request.app.settings["hostname"]
    user_uid = request.match_info["user_uid"]

    claims = utils.enforce_authorization(request.headers, request.app.settings)
    if not is_root(claims["groups"]) and not claims["sub"] == user_uid:  # is user
        raise web.HTTPForbidden(reason="Do not have rights to view user info")

    last_element = request.rel_url.query.get("last_element", "")

    if not await request.app.storage_backend.user_exists(user_uid):
        raise web.HTTPNotFound(reason="User does not exist")
    groups = await request.app.storage_backend.get_groups_of_user(
        user_uid, last_element
    )

    content = {}

    if groups:
        content["next"] = coreapi.Link(
            url=f"{hostname}/users/{user_uid}?last_element={groups[-1]}"
        )
        content["groups"] = [
            coreapi.Document(
                url=f"{hostname}/groups/{group}/", content={"group": group}
            )
            for group in groups
        ]

    return serialize(
        request,
        coreapi.Document(
            url=f"{hostname}/users/{user_uid}", title="User interface", content=content
        ),
    )
