"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize
from pasee.identity_providers.utils import get_identity_provider_with_capability

logger = logging.getLogger(__name__)


async def get_users(request: web.Request) -> web.Response:
    """Handlers for GET /users/, just describes that a POST is possible.
    """
    identity_provider = get_identity_provider_with_capability(
        request.app.settings, "register-user"
    )
    register_user_endpoint = await identity_provider.get_endpoint("register-user")
    return serialize(
        request,
        coreapi.Document(
            url="/users/",
            title="Users management interface",
            content={
                "Self service registration": coreapi.Link(
                    action="get",
                    title="Self service registration for identity provider",
                    description="Get more information on how to self register",
                    url=register_user_endpoint,
                )
            },
        ),
    )
