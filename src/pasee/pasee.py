"""Pasee main module.
"""

import os
from typing import Dict, Optional

from aiohttp import web
import pytoml as toml

from pasee.middlewares import verify_input_body_is_json
from pasee.middlewares import claim_user_authorization
from pasee import views
from pasee.groups import views as group_views
from pasee.tokens import views as token_views
from pasee.groups.backend import import_authorization_backend


class MissingSettings(ValueError):
    """A mandatory setting is missing from the configuration file.
    """


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
    auth_endpoints = [("/groups/", ("GET", "POST"))]

    settings = load_conf(settings_file, host, port, identity_backend_class)
    app = web.Application(
        middlewares=[
            verify_input_body_is_json,
            claim_user_authorization(
                urls=auth_endpoints,
                public_key=settings["public_key"],
                algorithm=settings["algorithm"],
            ),
        ]
    )
    app.settings = settings
    app.authorization_backend = import_authorization_backend(
        settings["authorization_backend"]["class"]
    )(settings["authorization_backend"]["options"])

    async def on_startup_wrapper(app):
        """Wrapper to call __aenter__.
        """
        await app.authorization_backend.__aenter__()

    async def on_cleanup_wrapper(app):
        """Wrapper to call __exit__.
        """
        await app.authorization_backend.__aexit__(None, None, None)

    app.on_startup.append(on_startup_wrapper)
    app.on_cleanup.append(on_cleanup_wrapper)

    app.add_routes(
        [
            web.get("/", views.get_root),
            web.get("/tokens/", token_views.get_tokens),
            web.post("/tokens/", token_views.post_token),
            web.get("/groups/", group_views.get_groups),
            web.post("/groups/", group_views.post_groups),
            web.get("/groups/{group_uid}/", group_views.get_group),
            web.post("/groups/{group_uid}/", group_views.post_group),
        ]
    )

    return app
