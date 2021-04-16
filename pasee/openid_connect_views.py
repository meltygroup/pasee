import json
from typing import Tuple, Optional
from aiohttp import web
from aioauth.server import AuthorizationServer
from aioauth.types import RequestMethod
from aioauth.config import Settings
from aioauth.base.database import BaseDB
from aioauth.models import Token, AuthorizationCode, Client
from aioauth.requests import (
    Query,
    Post,
    Request as OAuth2Request,
)
from aioauth.responses import Response as OAuth2Response
from aioauth.structures import CaseInsensitiveDict


class DB(BaseDB):
    """Class for interacting with the database. Used by `AuthorizationServer`.

    Here you need to override the methods that are responsible for creating tokens,
    creating authorization code, getting a client from the database, etc.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tokens_by_access_token = {}
        self.tokens_by_refresh_token = {}
        self.authorization_codes = {}

    async def save_token(self, token: Token):
        """Store ALL fields of the Token namedtuple in a db"""
        self.tokens_by_access_token[token.access_token] = token
        self.tokens_by_refresh_token[token.refresh_token] = token

    async def save_authorization_code(self, authorization_code: AuthorizationCode):
        """Store ALL fields of the AuthorizationCode namedtuple in a db"""
        self.authorization_codes[authorization_code.code] = authorization_code

    async def get_token(
        self,
        request: OAuth2Request,
        client_id: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> Optional[Token]:
        """Get token from the database by provided request from user.

        Returns:
            Token: if token exists in db.
            None: if no token in db.
        """
        if access_token:
            return self.tokens_by_access_token.get(access_token)
        if refresh_token:
            return self.tokens_by_refresh_token.get(refresh_token)
        return None

    async def get_client(
        self,
        request: OAuth2Request,
        client_id: str,
        client_secret: Optional[str] = None,
    ) -> Optional[Client]:
        """Get client record from the database by provided request from user.

        Returns:
            `Client` instance if client exists in db.
            `None` if no client in db.
        """
        if int(client_id) == 1:
            return Client(
                client_id=1,
                client_secret="foo",
                grant_types=["authorization_code"],
                response_types=["code"],
                redirect_uris=["https://mdk.fr/openid_connect"],
                scope="openid",
            )
        return None

    async def revoke_token(self, request: OAuth2Request, refresh_token: str) -> None:
        """Revokes an existing token. The `revoked` Flag of the Token must be
        set to True.

        """
        self.tokens_by_refresh_token[refresh_token].revoked = True

    async def get_authorization_code(
        self, request: OAuth2Request, client_id: str, code: str
    ) -> Optional[AuthorizationCode]:
        return self.authorization_codes[code]

    async def delete_authorization_code(self, *args, **kwargs) -> None:
        del self.authorization_codes[code]

    async def authenticate(self, request: OAuth2Request) -> bool:
        """Basic auth client authentication."""
        return True


server = AuthorizationServer(db=DB())


async def to_oauth2_request(request: web.Request) -> OAuth2Request:
    """Convert aiohttp request instance to OAuth2Request instance."""
    return OAuth2Request(
        settings=Settings(INSECURE_TRANSPORT=True),
        method=RequestMethod[request.method],
        headers=request.headers,
        post=Post(**dict(await request.post())),
        query=Query(**dict(request.query)),
        url=request.url,
        user=None,
    )


async def to_aiohttp_response(oauth2_response: OAuth2Response) -> web.Response:
    """Converts OAuth2Response instance to aiohttp Response instance"""
    response_content = (
        oauth2_response.content._asdict() if oauth2_response.content is not None else {}
    )
    headers = dict(oauth2_response.headers)
    status_code = oauth2_response.status_code
    return web.Response(
        text=json.dumps(response_content, indent=4), status=status_code, headers=headers
    )


async def authorize(request: web.Request) -> web.Response:
    """Endpoint to interact with the resource owner and obtain an authorization grant.

    See Section 4.1.1: https://tools.ietf.org/html/rfc6749#section-4.1.1
    """
    #
    # C'est ici qu'on doit fournir du HTML à l'utilisateur avec un
    # formulaire de login ET un formulaire de consentement.
    #
    # oauth2_request DOIT avoir l'attribut `user` pour pouvoir continuer.
    oauth2_request: OAuth2Request = await to_oauth2_request(request)
    oauth2_response: OAuth2Response = await server.create_authorization_response(
        oauth2_request
    )

    return await to_aiohttp_response(oauth2_response)


async def post_token(request: web.Request) -> web.Response:
    """Endpoint to obtain an access and/or ID token by presenting an authorization grant or refresh token.

    See Section 4.1.3: https://tools.ietf.org/html/rfc6749#section-4.1.3
    """
    oauth2_request: OAuth2Request = await to_oauth2_request(request)
    oauth2_response: OAuth2Response = await server.create_token_response(oauth2_request)

    return await to_aiohttp_response(oauth2_response)


async def get_introspect(request: web.Request) -> web.Response:
    """Endpoint returns information about a token.

    See Section 2.1: https://tools.ietf.org/html/rfc7662#section-2.1
    """
    oauth2_request: OAuth2Request = await to_oauth2_request(request)
    oauth2_response: OAuth2Response = await server.create_token_introspection_response(
        oauth2_request
    )

    return await to_aiohttp_response(oauth2_response)
