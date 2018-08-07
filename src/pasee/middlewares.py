"""middleswares for the pasee server
"""

import json
from typing import Callable

from aiohttp import web


@web.middleware
async def verify_input_body_is_json(
    request: web.Request, handler: Callable
) -> Callable:
    """
    Middleware to verify that input body is of json format
    """
    if request.has_body:
        try:
            request.data = await request.json()
        except json.decoder.JSONDecodeError:
            raise web.HTTPUnprocessableEntity(reason="Malformed JSON.")
    return await handler(request)
