"""Views for users ressource in Pasee server, implementing:

- GET /users/
- POST /users/
"""
import logging

import coreapi
from aiohttp import web

from pasee.serializers import serialize


logger = logging.getLogger(__name__)


async def get_users(request: web.Response) -> web.Response:
    """Handlers for GET /users/, just describes that a POST is possible.
    """
    return serialize(
        request,
        coreapi.Document(
            url="/users/",
            title="Users management interface",
            content={
                "self service registration": coreapi.Link(
                    action="post",
                    title="Self service registration",
                    description="POSTing to this endpoint to create an user",
                    fields=[
                        coreapi.Field(name="username", required=True),
                        coreapi.Field(name="password", required=True),
                    ],
                ),
            },
        ),
    )


async def post_users(request: web.Response) -> web.Response:
    """Handler for post /users/, use to create a user
    """
