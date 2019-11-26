"""Pasee main module.
"""

import logging

from aiohttp import web
import aiohttp_cors

from pasee.middlewares import (
    verify_input_body_is_json,
    transform_unauthorized,
    coreapi_error_middleware,
    security_headers,
)
from pasee import views
from pasee.groups import views as group_views
from pasee.tokens import views as token_views
from pasee.users import views as user_views
from pasee.utils import import_class

logging.basicConfig(level=logging.DEBUG)


def identification_app(settings,):
    """Identification provider entry point: builds and run a webserver.
    """

    app = web.Application(
        middlewares=[
            verify_input_body_is_json,
            transform_unauthorized,
            coreapi_error_middleware,
            security_headers,
        ]
    )

    app["settings"] = settings
    app["storage_backend"] = import_class(settings["storage_backend"]["class"])(
        settings["storage_backend"]["options"]
    )

    async def on_startup_wrapper(app):
        """Wrapper to call __aenter__.
        """
        await app["storage_backend"].__aenter__()

    async def on_cleanup_wrapper(app):
        """Wrapper to call __exit__.
        """
        await app["storage_backend"].__aexit__(None, None, None)

    app.on_startup.append(on_startup_wrapper)
    app.on_cleanup.append(on_cleanup_wrapper)

    app.add_routes(
        [
            web.get("/", views.get_root, name="get_root"),
            web.get("/public-key/", views.get_public_key, name="get_public_key"),
            web.get("/tokens/", token_views.get_tokens, name="get_tokens"),
            web.post("/tokens/", token_views.post_token, name="post_tokens"),
            web.get("/users/", user_views.get_users),
            web.get("/users/{username}", user_views.get_user),
            web.delete("/users/{username}", user_views.delete_user),
            web.patch("/users/{username}", user_views.patch_user),
            web.get("/groups/", group_views.get_groups),
            web.post("/groups/", group_views.post_groups),
            web.get("/groups/{group_uid}/", group_views.get_group),
            web.delete("/groups/{group_uid}/", group_views.delete_group),
            web.post("/groups/{group_uid}/", group_views.post_group),
            web.delete(
                "/groups/{group_uid}/{username}/", group_views.delete_group_member
            ),
        ]
    )

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "OPTIONS", "PUT", "POST", "DELETE", "PATCH"],
            )
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)

    return app
