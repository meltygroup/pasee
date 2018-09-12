"""Utils for handling identity providers
"""
from aiohttp import web

from pasee.utils import import_class

BACKENDS = {"kisee": "identity_providers.kisee.KiseeIdentityProvider"}


def get_identity_provider_or_raise(identity_provider_input, idps_settings):
    """Returns an identity provider object or raise a web response error"""
    if not identity_provider_input:
        raise web.HTTPBadRequest(reason="Missing identity provider input")

    identity_provider_path = BACKENDS.get(identity_provider_input, None)
    identity_provider_settings = idps_settings.get(identity_provider_input, None)

    if not identity_provider_path:
        raise web.HTTPBadRequest(reason="Identity provider not implemented")
    if not identity_provider_settings:
        raise web.HTTPBadRequest(reason="Identity provider settings not set in server")

    return import_class(identity_provider_path)(identity_provider_settings)
