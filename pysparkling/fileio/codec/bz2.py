import bz2
import io
import logging

from .codec import Codec

log = logging.getLogger(__name__)


class Bz2(Codec):
    """Implementation of :class:`.Codec` for bz2 compression."""

    def compress(self, stream):
        return io.BytesIO(bz2.compress(b''.join(stream)))

    def decompress(self, stream):
        return io.BytesIO(bz2.decompress(stream.read()))
