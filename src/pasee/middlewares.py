"""middleswares for the pasee server
"""

import json
from typing import Callable

from aiohttp import web

from pasee import Unauthorized


@web.middleware
async def verify_input_body_is_json(
    request: web.Request, handler: Callable
) -> Callable:
    """
    Middleware to verify that input body is of json format
    """
    if request.has_body:
        try:
            await request.json()
        except json.decoder.JSONDecodeError:
            raise web.HTTPBadRequest(reason="Malformed JSON.")
    return await handler(request)


@web.middleware
async def transform_unauthorized(request: web.Request, handler: Callable) -> Callable:
    """Middleware to except pasee.Unauthorized exceptions and transform
    them to proper HTTP exceptions.
    """
    try:
        return await handler(request)
    except Unauthorized as err:
        raise web.HTTPBadRequest(
            reason=err.reason, headers={"WWW-Authenticate": "Bearer"}
        )
