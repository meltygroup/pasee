"""Identity provider for Kisee
"""
import json

import aiohttp
from aiohttp import web
import jwt

from pasee.identity_providers.backend import IdentityProviderBackend


class KiseeIdentityProvider(IdentityProviderBackend):
    """Kisee Identity Provider
    """

    def __init__(self, settings, **kwargs) -> None:
        super().__init__(settings, **kwargs)
        self.public_keys = self.settings["settings"]["public_keys"]
        self.endpoint = self.settings["endpoint"]
        self.name = "kisee"

    async def _identify_to_kisee(self, data):
        """Async request to identify to kisee"""
        create_token_endpoint = self.endpoint + "/jwt/"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                create_token_endpoint,
                headers={"Content-Type": "application/json"},
                json=data,
            ) as response:

                if response.status == 403:
                    raise web.HTTPForbidden(reason="Can not authenticate on kisee")
                elif response.status != 201:
                    raise web.HTTPBadGateway(
                        reason="Something went wrong with identity provider"
                    )

                kisee_response = await response.text()
                kisee_response = json.loads(kisee_response)

        return kisee_response

    def _decode_token(self, token: str):
        """Decode token with public keys
        """
        for public_key in self.public_keys:
            try:
                decoded = jwt.decode(token, public_key)
                return decoded
            except ValueError:
                pass
        raise web.HTTPInternalServerError()

    async def authenticate_user(self, data):
        if not all(key in data.keys() for key in {"login", "password"}):
            raise web.HTTPBadRequest(
                reason="Missing login or password fields for kisee authentication"
            )
        kisee_response = await self._identify_to_kisee(data)

        # TODO use header location instead to retrieve token
        # kisee_headers = response.headers
        # token_location = kisee_headers["Location"]

        token = kisee_response["tokens"][0]
        return self._decode_token(token)

    async def register_user(self, data) -> str:
        if not all(key in data.keys() for key in ["username", "password"]):
            raise web.HTTPBadRequest(
                reason="Missing required fields for kisee registration"
            )

        register_user_endpoint = self.endpoint + "/users/"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                register_user_endpoint,
                headers={"Content-Type": "application/json"},
                json=data,
            ) as response:
                if response.status != 201:
                    raise web.HTTPFailedDependency(
                        reason="Can not register user in Kisee"
                    )
        return data["username"]

    def get_name(self):
        return self.name
