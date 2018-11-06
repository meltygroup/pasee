"""Identity provider for Twitter
"""
from typing import Optional

from aiohttp import web
from aioauth_client import TwitterClient

from pasee.identity_providers.backend import IdentityProviderBackend
from pasee.identity_providers.backend import Claims, LoginCredentials


class TwitterIdentityProvider(IdentityProviderBackend):
    """Twitter Identity Provider
    """

    def __init__(self, settings, **kwargs) -> None:
        super().__init__(settings, **kwargs)
        self.name = "twitter"
        self.consumer_key = self.settings["settings"]["consumer_key"]
        self.consumer_secret = self.settings["settings"]["consumer_secret"]
        self.callback_url = self.settings["settings"]["callback_url"]
        self.client = TwitterClient(
            consumer_key=self.consumer_key, consumer_secret=self.consumer_secret
        )

    async def authenticate_user(self, data: LoginCredentials, step: int = 1) -> Claims:
        """Twitter authenticate user returns a link that user use to for
        for identity verification
        """
        if step == 1:
            request_token, _, data = await self.client.get_request_token(
                oauth_callback=self.callback_url
            )
            authorize_url = self.client.get_authorize_url(request_token)
            return {"authorize_url": authorize_url}
        elif step == 2:
            self.client.oauth_token = data["oauth_token"]
            oauth_token, _, oauth_data = await self.client.get_access_token(
                data["oauth_verifier"], request_token=data["oauth_token"]
            )
            return {"access_token": oauth_token, "sub": oauth_data["user_id"]}
        else:
            raise ValueError("only step 1 or 2 is available")

    async def get_endpoint(self, action: Optional[str] = None):

        raise web.HTTPNotImplemented(
            reason="No other action possible in twitter but authentication"
        )

    def get_name(self):
        return self.name
