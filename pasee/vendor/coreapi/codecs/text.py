# coding: utf-8
from pasee.vendor.coreapi.codecs.base import BaseCodec


class TextCodec(BaseCodec):
    media_type = "text/*"
    format = "text"

    def decode(self, bytestring, **options):
        return bytestring.decode("utf-8")
