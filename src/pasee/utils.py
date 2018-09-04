"""Some functions not directly linked with the core of pasee but still usefull.
"""
from importlib import import_module
from typing import List, Tuple

import jwt
from aiohttp import web


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


def enforce_authorization(request: web.Request) -> Tuple[str, List[str]]:
    """claim user authorization middleware handler written as a standalone
    function to allow easier mocking for test
    """

    if not request.headers.get("Authorization"):
        raise web.HTTPBadRequest(
            reason="missing_authorization_header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = request.headers.get("Authorization").strip().split(" ")
    except ValueError:
        raise web.HTTPBadRequest(
            reason="unable_to_retrieve_scheme_and_token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if scheme != "Bearer":
        raise web.HTTPBadRequest(
            reason="invalid_authorization_scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        decoded = jwt.decode(
            token, request.app.settings["public_key"], request.app.settings["algorithm"]
        )
        return decoded["sub"], decoded["groups"]
    except jwt.ExpiredSignatureError:
        raise web.HTTPBadRequest(
            reason="expired_signature", headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError:
        raise web.HTTPBadRequest(
            reason="unable_to_decode_token", headers={"WWW-Authenticate": "Bearer"}
        )
