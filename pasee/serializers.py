"""Serialisers using coreapi, the idea is to (in the future) provide
various representations of our resources like mason, json-ld, hal, ...

"""
from aiohttp import web

from pasee.vendor import coreapi


def serialize(
    request: web.Request, document: coreapi.Document, status=200, headers=None
) -> web.Response:
    """Serialize the given document according to the Accept header of the
    given request.
    """
    del request
    codec = coreapi.utils.negotiate_encoder([coreapi.codecs.CoreJSONCodec()], None)
    content = codec.dump(document)
    return web.Response(
        body=content, content_type=codec.media_type, headers=headers, status=status
    )
