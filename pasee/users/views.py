"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import functools
import logging
from typing import List, Tuple
from urllib.parse import parse_qs

from aiohttp import web

from pasee import Unauthorized
from pasee.serializers import serialize
from pasee.vendor import coreapi
from pasee import utils
from pasee.groups.utils import is_root

logger = logging.getLogger(__name__)


def cached():  # pragma: no cover  # needs a running kisee
    """Simply cache the result of a coroutine."""
    _cache = None

    def wrapper(func):
        @functools.wraps(func)
        async def _cached(*args, **kwargs):
            nonlocal _cache
            if _cache is None:
                _cache = await func(*args, **kwargs)
            return _cache

        return _cached

    return wrapper


async def _get_users(request: web.Request) -> Tuple[List[coreapi.Error], List[str]]:
    """Get users, if requester is root."""
    try:
        if utils.is_root(request):
            after = request.rel_url.query.get("after", "")
            return [], await request.app["storage_backend"].get_users(after)
    except Unauthorized as err:
        return [coreapi.Error(content={"reason": err.reason})], []
    return [], []


async def get_users(request: web.Request) -> web.Response:
    """Handlers for GET /users/, just describes that a POST is possible."""
    hostname = request.app["settings"]["hostname"]
    errors, users = await _get_users(request)
    last_element = users[-1] if users else None
    content = {
        "users": [
            coreapi.Document(
                url=f"{hostname}/users/{user}/", content={"username": user}
            )
            for user in users
        ],
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
        headers={"Vary": "Origin"},
    )


async def get_user(request: web.Request) -> web.Response:
    """Handlers for GET /users/{username}
    List groups of {username}
    """
    hostname = request.app["settings"]["hostname"]
    username = request.match_info["username"]

    claims = utils.enforce_authorization(request.headers, request.app["settings"])
    if not is_root(claims["groups"]) and not claims["sub"] == username:  # is user
        raise web.HTTPForbidden(reason="Do not have rights to view user info")

    last_element = request.rel_url.query.get("last_element", "")

    user = await request.app["storage_backend"].get_user(username)
    if not user:
        raise web.HTTPNotFound(reason="User does not exist")

    groups = await request.app["storage_backend"].get_groups_of_user(
        username, last_element
    )

    content = user
    content["patch"] = coreapi.Link(
        action="patch",
        title="Patch fields of user",
        description="A method to patch fields of user",
        fields=[coreapi.Field(name="is_banned")],
    )

    if groups:
        content["next"] = coreapi.Link(
            url=f"{hostname}/users/{username}?last_element={groups[-1]}"
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
            url=f"{hostname}/users/{username}", title="User interface", content=content
        ),
        headers={"Vary": "Origin"},
    )


async def patch_user(request: web.Request) -> web.Response:
    """Handlers for PATCH /users/{username}
    Patch an user
    """
    username = request.match_info["username"]

    claims = utils.enforce_authorization(request.headers, request.app["settings"])
    if not is_root(claims["groups"]):
        raise web.HTTPForbidden(reason="Do not have rights to patch")

    user = await request.app["storage_backend"].get_user(username)
    if not user:
        raise web.HTTPNotFound(reason="User does not exist")

    input_data = await request.json()
    if "username" in input_data:
        raise web.HTTPBadRequest(reason="can not patch username")
    if "is_banned" in input_data:
        ban = input_data["is_banned"]
        await request.app["storage_backend"].ban_user(username, ban)
    return web.Response(status=204)


async def delete_user(request: web.Request) -> web.Response:
    """Handlers for DELETE /users/{username}
    Delete {username}
    """
    username = request.match_info["username"]
    claims = utils.enforce_authorization(request.headers, request.app["settings"])
    if not is_root(claims["groups"]):
        raise web.HTTPForbidden(reason="Do not have rights to delete user")
    await request.app["storage_backend"].delete_user(username)
    return web.Response(status=204)
