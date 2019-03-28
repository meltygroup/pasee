"""Views for the Pasee server, implementing:

- GET /
"""

import json
import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def get_root(request: web.Request) -> web.Response:
    """https://tools.ietf.org/html/draft-nottingham-json-home-06
    """
    hostname = request.app.settings["hostname"]
    home = {
        "api": {
            "title": "Identification Manager",
            "links": {
                "author": "mailto:julien@palard.fr",
                "describedBy": "https://doc.meltylab.fr",
            },
        },
        "resources": {
            "public-key": {"href": f"{hostname}/public-key/"},
            "tokens": {
                "hints": {"allow": ["GET", "POST"]},
                "href": f"{hostname}/tokens/",
            },
            "groups": {
                "href": f"{hostname}/groups/",
                "hints": {"allow": ["GET", "POST"]},
            },
            "group": {
                "hrefTemplate": f"{hostname}/groups/{{group_uid}}/",
                "hrefVars": {"group_uid": "group unique id"},
                "hints": {"allow": ["GET", "POST", "DELETE"]},
            },
            "users": {
                "href": f"{hostname}/users/",
                "hints": {"allow": ["GET", "DELETE", "PATCH"]},
            },
        },
    }
    return web.Response(
        body=json.dumps(home, indent=4),
        headers={"Vary": "Origin"},
        content_type="application/json-home+json",
    )


async def get_public_key(request: web.Request) -> web.Response:
    """Get public key
    """
    public_key = request.app.settings["public_key"]
    algorithm = request.app.settings["algorithm"]
    return web.Response(
        body=json.dumps({"public_key": public_key, "algorithm": algorithm}),
        headers={"Vary": "Origin"},
        content_type="application/json",
    )
