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
    del request
    return web.Response(
        body=json.dumps(
            {
                "api": {
                    "title": "Identification Manager",
                    "links": {
                        "author": "mailto:julien@palard.fr",
                        "describedBy": "https://doc.meltylab.fr",
                    },
                },
                "resources": {
                    "tokens": {"hints": {"allow": ["GET", "POST"]}, "href": "/tokens/"},
                    "groups": {"href": "/groups/", "hints": {"allow": ["GET", "POST"]}},
                    "group": {
                        "hrefTemplate": "/groups/{group_uid}",
                        "hrefVars": {
                            "group_uid": "doc_to_what_group_uid_means.that.com"
                        },
                        "hints": {"allow": ["GET", "PUT", "DELETE"]},
                    },
                },
            }
        ),
        content_type="application/json-home",
    )
