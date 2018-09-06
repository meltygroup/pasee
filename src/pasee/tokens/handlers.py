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
        hours_to_add=1
    )
    access_token = jwt.encode(claims, private_key, algorithm=algorithm)

    claims["jti"], claims["exp"] = create_jti_and_expiration_values(  # type: ignore
        hours_to_add=24
    )
    claims["refresh_token"] = True
    refresh_token = jwt.encode(claims, private_key, algorithm=algorithm)
    return access_token, refresh_token


async def generate_claims_with_identity_provider(request: web.Request) -> dict:
    """Use identity provider provided by user to authenticate.
    And use identity against authorization server database to retrieve claims
    """
    input_data = await request.json()
    if not all(key in input_data.keys() for key in ["data", "identity_provider"]):
        raise web.HTTPUnprocessableEntity(reason="missing_required_input_fields")
    if input_data["identity_provider"] not in identity_providers.BACKENDS:
        raise web.HTTPUnprocessableEntity(reason="Identity provider not implemented")

    identity_provider_path = identity_providers.BACKENDS[
        input_data["identity_provider"]
    ]
    identity_provider_settings = request.app.settings["idps"][
        input_data["identity_provider"]
    ]
    identity_provider = import_class(identity_provider_path)(identity_provider_settings)

    decoded = await identity_provider.authenticate_user(input_data["data"])

    decoded["sub"] = f"{input_data['identity_provider']}-{decoded['sub']}"
    if not await request.app.authorization_backend.user_exists(decoded["sub"]):
        raise web.HTTPNotFound(
            reason="user_does_not_exist_in_our_authorization_service"
        )
    decoded[
        "groups"
    ] = await request.app.authorization_backend.get_authorizations_for_user(
        decoded["sub"]
    )
    return decoded
