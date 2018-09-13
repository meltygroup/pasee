"""Some functions not directly linked with the core of pasee but still usefull.
"""
from typing import Mapping, Any

from importlib import import_module

import jwt
from aiohttp import web
from pasee import Unauthorized


def import_class(dotted_path: str) -> type:
    """Import a dotted module path and return the attribute/class
    designated by the last name in the path. Raise ImportError if the
    import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err


def enforce_authorization(request: web.Request) -> Mapping[str, Any]:
    """claim user authorization middleware handler written as a standalone
    function to allow easier mocking for test
    """

    if not request.headers.get("Authorization"):
        raise Unauthorized("Missing authorization header")
    try:
        scheme, token = request.headers.get("Authorization").strip().split(" ")
    except ValueError as err:
        raise Unauthorized("Malformed authorization header") from err
    if scheme != "Bearer":
        raise Unauthorized("Expected Bearer token")
    try:
        return jwt.decode(
            token, request.app.settings["public_key"], request.app.settings["algorithm"]
        )
    except jwt.ExpiredSignatureError as err:
        raise Unauthorized("Expired signature") from err
    except ValueError as err:
        raise Unauthorized("Invalid token") from err
