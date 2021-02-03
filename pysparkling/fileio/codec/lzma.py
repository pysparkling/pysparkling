from io import BytesIO
import logging
import lzma

from .codec import Codec

log = logging.getLogger(__name__)


class Lzma(Codec):
    """Implementation of :class:`.Codec` for lzma compression.

    Needs Python >= 3.3.
    """

    def __init__(self):
        if lzma is None:
            log.warning('LZMA codec not supported. It is only supported '
                        'in Python>=3.3. Not compressing streams.')
        super().__init__()

    def compress(self, stream):
        if lzma is None:
            return Codec.compress(self, stream)

        return BytesIO(lzma.compress(stream.read()))

    def decompress(self, stream):
        if lzma is None:
            return Codec.decompress(self, stream)

        return BytesIO(lzma.decompress(stream.read()))
