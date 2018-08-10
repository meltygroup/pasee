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
