"""middleswares for the pasee server
"""

import json
from typing import Callable

from aiohttp import web

from pasee import Unauthorized, Unauthenticated
from pasee.serializers import serialize


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
    except (Unauthorized, Unauthenticated) as err:
        raise web.HTTPBadRequest(
            reason=err.reason, headers={"WWW-Authenticate": "Bearer"}
        )


@web.middleware
async def coreapi_error_middleware(request, handler):
    """Implementation of:
    http://www.coreapi.org/specification/transport/#coercing-4xx-and-5xx-responses-to-errors
    """
    try:
        return await handler(request)
    except web.HTTPException as ex:
        return serialize(
            request, {"_type": "error", "_meta": {"title": ex.reason}}, ex.status
        )


SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'",
    "Referrer-Policy": "origin-when-cross-origin, strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubdomains; preload",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "deny",
    "X-XSS-Protection": "1; mode=block",
}


@web.middleware
async def security_headers(request, handler):
    """Add some security headers like CSP, Referrer-Policy and so on.
    """
    response = await handler(request)
    response.headers.update(SECURITY_HEADERS)
    return response
