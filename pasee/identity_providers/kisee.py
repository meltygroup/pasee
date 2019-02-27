"""Identity provider for Kisee
"""
import json
from typing import Optional, Dict

import aiohttp
from aiohttp import web
import jwt

from pasee.identity_providers.backend import IdentityProviderBackend
from pasee.identity_providers.backend import Claims, LoginCredentials


class KiseeIdentityProvider(IdentityProviderBackend):
    """Kisee Identity Provider
    """

    def __init__(self, settings, **kwargs) -> None:
        super().__init__(settings, **kwargs)
        self.public_keys = self.settings["settings"]["public_keys"]
        self.endpoint = self.settings["endpoint"]
        self.name = self.settings["name"]
        self.action_to_endpoint: Dict = dict()

    async def _identify_to_kisee(self, data: LoginCredentials):
        """Async request to identify to kisee"""
        create_token_endpoint = await self.get_endpoint("create-token")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                create_token_endpoint,
                headers={"Content-Type": "application/json"},
                json=data,
            ) as response:

                if response.status == 403:
                    raise web.HTTPForbidden(reason="Can not authenticate on kisee")
                if response.status != 201:
                    raise web.HTTPBadGateway(
                        reason="Something went wrong with identity provider"
                    )

                kisee_response = await response.text()
                kisee_response = json.loads(kisee_response)

        return kisee_response

    def _decode_token(self, token: str):
        """Decode token with public keys.
        """
        for public_key in self.public_keys:
            try:
                decoded = jwt.decode(token, public_key, algorithms="ES256")
                return decoded
            except (ValueError, jwt.DecodeError):
                pass
        raise web.HTTPInternalServerError()

    async def authenticate_user(self, data: LoginCredentials, step: int = 1) -> Claims:
        if not all(key in data.keys() for key in {"login", "password"}):
            raise web.HTTPBadRequest(
                reason="Missing login or password fields for kisee authentication"
            )
        kisee_response = await self._identify_to_kisee(data)

        # TODO use header location instead to retrieve token
        # kisee_headers = response.headers
        # token_location = kisee_headers["Location"]

        token = kisee_response["tokens"][0]
        decoded = self._decode_token(token)
        decoded["sub"] = f"{self.name}-{decoded['sub']}"
        return decoded

    async def get_endpoint(self, action: Optional[str] = None):

        if not action:
            return self.endpoint

        if action in self.action_to_endpoint:
            return self.action_to_endpoint[action]

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.endpoint) as response:
                    root = await response.json()
            except aiohttp.client_exceptions.ClientConnectorError:
                raise web.HTTPServiceUnavailable(reason="kisee not responding")

        self.action_to_endpoint[action] = root["actions"][action]["href"]
        return self.action_to_endpoint[action]

    def get_name(self):
        return self.name
