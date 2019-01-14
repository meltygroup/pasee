"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import logging
from typing import List

import coreapi
from aiohttp import web

from pasee import Unauthorized
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
    try:
        claims = utils.enforce_authorization(request.headers, request.app.settings)
        if is_root(claims["groups"]):
            last_element = request.rel_url.query.get("last_element", "")
            users = await request.app.storage_backend.get_users(last_element)
    except Unauthorized:
        pass

    return serialize(
        request,
        coreapi.Document(
            url=f"{hostname}/users/",
            title="Users management interface",
            content={
                "users": users,
                "Self service registration": coreapi.Link(
                    action="get",
                    title="Self service registration for identity provider",
                    description="Get more information on how to self register",
                    url=register_user_endpoint,
                ),
            },
        ),
    )
