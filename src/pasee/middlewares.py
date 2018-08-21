"""middleswares for the pasee server
"""

import json
from typing import Callable

import jwt
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


def claim_user_authorization(urls, public_key, algorithm):
    """
    """

    @web.middleware
    async def middleware(request, handler):
        for url, methods in urls:

            if not request.path.startswith(url):
                continue
            if request.method not in methods:
                break

            if not request.headers.get("Authorization"):
                raise web.HTTPBadRequest(reason="missing_authorization_header")

            try:
                scheme, token = request.headers.get("Authorization").strip().split(" ")
            except ValueError:
                raise web.HTTPForbidden(reason="invalid_authorization_header")
            if scheme != "Bearer":
                raise web.HTTPForbidden(reason="invalid_authorization_header")
            try:
                decoded = jwt.decode(token, public_key, algorithm)
                request.user = decoded["sub"]
                request.groups = decoded["groups"]
            except jwt.exceptions.ExpiredSignatureError:
                raise web.HTTPUnauthorized(reason="expired_signature")
            except ValueError:
                raise web.HTTPUnauthorized()

            return await handler(request)
        return await handler(request)

    return middleware
