"""Pasee main module.
"""

import os
from typing import Dict, Optional

from aiohttp import web
import pytoml as toml

from pasee import views
from pasee.middlewares import verify_input_body_is_json


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
    app = web.Application(middlewares=[verify_input_body_is_json])
    app.settings = load_conf(settings_file, host, port, identity_backend_class)

    app.add_routes(
        [
            web.get("/", views.get_root),
            web.get("/token/", views.get_tokens),
            web.post("/token/", views.post_token),
        ]
    )

    return app
