"""Pasee main module.
"""

import os
from typing import Dict, Optional

from aiohttp import web
import aiohttp_cors
import pytoml as toml

from pasee.middlewares import verify_input_body_is_json, transform_unauthorized
from pasee import views, MissingSettings
from pasee.groups import views as group_views
from pasee.tokens import views as token_views
from pasee.users import views as user_views
from pasee.utils import import_class


def load_conf(
    settings_path: Optional[str],
    host: str = None,
    port: int = None,
    identity_backend_class: str = None,
) -> Dict:
    """Search for a settings.toml file and load it.
    """
    del identity_backend_class
    candidates: tuple
    if settings_path:
        candidates = (
            settings_path,
            os.path.join(os.getcwd(), settings_path),
            os.path.join(os.getcwd(), "settings.toml"),
            os.path.expanduser("~/settings.toml"),
            os.path.expanduser(os.path.join("~/", settings_path)),
            "/etc/settings.toml",
            os.path.join("/etc/", settings_path),
        )
    else:
        candidates = (
            os.path.join(os.getcwd(), "settings.toml"),
            os.path.expanduser("~/settings.toml"),
            "/etc/settings.toml",
        )
    for candidate in candidates:
        if os.path.exists(candidate):
            with open(candidate) as candidate_file:
                settings = toml.load(candidate_file)
    if host:
        settings["host"] = host
    if "host" not in settings:
        settings["host"] = "127.0.0.1"
    if port:
        settings["port"] = port
    if "port" not in settings:
        settings["port"] = 8140
    for mandatory_setting in {"private_key", "public_key", "identity_providers"}:
        if mandatory_setting not in settings:
            raise MissingSettings(f"No {mandatory_setting} in settings, see README.md")
    settings["idps"] = {idp["name"]: idp for idp in settings["identity_providers"]}
    return settings


def identification_app(
    settings_file: str = None,
    host: str = None,
    port: int = None,
    identity_backend_class: str = None,
):
    """Identification provider entry point: builds and run a webserver.
    """

    settings = load_conf(settings_file, host, port, identity_backend_class)
    app = web.Application(
        middlewares=[verify_input_body_is_json, transform_unauthorized]
    )

    app.settings = settings
    app.storage_backend = import_class(settings["storage_backend"]["class"])(
        settings["storage_backend"]["options"]
    )

    async def on_startup_wrapper(app):
        """Wrapper to call __aenter__.
        """
        await app.storage_backend.__aenter__()

    async def on_cleanup_wrapper(app):
        """Wrapper to call __exit__.
        """
        await app.storage_backend.__aexit__(None, None, None)

    app.on_startup.append(on_startup_wrapper)
    app.on_cleanup.append(on_cleanup_wrapper)

    app.add_routes(
        [
            web.get("/", views.get_root, name="get_root"),
            web.get("/public-key/", views.get_public_key),
            web.get("/tokens/", token_views.get_tokens, name="get_tokens"),
            web.post("/tokens/", token_views.post_token, name="post_tokens"),
            web.get("/users/", user_views.get_users),
            web.get("/groups/", group_views.get_groups),
            web.post("/groups/", group_views.post_groups),
            web.get("/groups/{group_uid}/", group_views.get_group),
            web.delete("/groups/{group_uid}/", group_views.delete_group),
            web.post("/groups/{group_uid}/", group_views.post_group),
            web.delete(
                "/groups/{group_uid}/{member_uid}/", group_views.delete_group_member
            ),
        ]
    )

    allowed_cors = {"get_root", "get_tokens", "post_tokens"}

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*"
            )
        },
    )

    for route in list(app.router.routes()):
        if route.name in allowed_cors:
            cors.add(route)

    return app
