"""Hanlers for tokens
"""
from datetime import datetime, timedelta

import jwt
import shortuuid
from aiohttp import web

from pasee.identity_providers import backend as identity_providers
from pasee.utils import import_class


def create_jti_and_expiration_values(hours_to_add: int):
    """Returns new uuid and expiration time
    """
    return shortuuid.uuid(), datetime.utcnow() + timedelta(hours=hours_to_add)


def generate_access_token_and_refresh_token_pairs(claims, private_key, algorithm):
    """Create new access token with refresh token
    """
    claims["jti"], claims["exp"] = create_jti_and_expiration_values(  # type: ignore
        hours_to_add=24
    )
    access_token = jwt.encode(claims, private_key, algorithm=algorithm)

    claims["jti"], claims["exp"] = create_jti_and_expiration_values(  # type: ignore
        hours_to_add=720
    )
    del claims["groups"]
    claims["refresh_token"] = True
    refresh_token = jwt.encode(claims, private_key, algorithm=algorithm)
    return access_token, refresh_token


async def authenticate_with_identity_provider(request: web.Request) -> dict:
    """Use identity provider provided by user to authenticate.
    """
    input_data = await request.json()

    identity_provider_input = request.rel_url.query.get("idp", None)
    if not identity_provider_input:
        raise web.HTTPBadRequest(
            reason="Identity provider not provided in query string"
        )
    if identity_provider_input not in identity_providers.BACKENDS:
        raise web.HTTPBadRequest(reason="Identity provider not implemented")

    identity_provider_path = identity_providers.BACKENDS[identity_provider_input]
    identity_provider_settings = request.app.settings["idps"][identity_provider_input]
    identity_provider = import_class(identity_provider_path)(identity_provider_settings)

    decoded = await identity_provider.authenticate_user(input_data)
    decoded["sub"] = f"{identity_provider.get_name()}-{decoded['sub']}"
    return decoded


async def handle_oauth_callback(identity_provider_input: str, request: web.Request):
    """Callback handler for oauth protocol
    """
    if identity_provider_input not in identity_providers.BACKENDS:
        raise web.HTTPBadRequest(reason="Identity provider not implemented")
    identity_provider_path = identity_providers.BACKENDS[identity_provider_input]
    identity_provider_settings = request.app.settings["idps"][identity_provider_input]
    identity_provider = import_class(identity_provider_path)(identity_provider_settings)
    idp_claims = await identity_provider.get_access_token(
        {
            "oauth_verifier": request.rel_url.query.get("oauth_verifier"),
            "oauth_token": request.rel_url.query.get("oauth_token"),
        }
    )

    sub = f"{identity_provider_input}-{idp_claims['sub']}"
    if not await request.app.authorization_backend.user_exists(sub):
        raise web.HTTPNotFound(reason="User does not exist in our authorization server")
    groups = await request.app.authorization_backend.get_authorizations_for_user(sub)

    pasee_claims = {
        "iss": request.app.settings["jwt"]["iss"],
        "sub": f"{identity_provider_input}-{idp_claims['sub']}",
        "groups": groups,
    }
    return generate_access_token_and_refresh_token_pairs(
        pasee_claims,
        request.app.settings["private_key"],
        algorithm=request.app.settings["algorithm"],
    )
