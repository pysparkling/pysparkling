import logging

from .bz2 import Bz2
from .codec import Codec
from .gz import Gz
from .lzma import Lzma
from .sevenz import SevenZ
from .tar import Tar, TarBz2, TarGz
from .zip import Zip

log = logging.getLogger(__name__)

FILE_ENDINGS = [
    (('.tar',), Tar),
    (('.tar.gz',), TarGz),
    (('.tar.bz2',), TarBz2),
    (('.gz',), Gz),
    (('.zip',), Zip),
    (('.bz2',), Bz2),
    (('.lzma', '.xz'), Lzma),
    (('.7z',), SevenZ),
]


class NoCodec(Codec):
    pass


def get_codec(path):
    """Find the codec implementation for this path."""
    if '.' not in path or path.rfind('/') > path.rfind('.'):
        return Codec

    for endings, codec_class in FILE_ENDINGS:
        if any(path.endswith(e) for e in endings):
            log.debug('Using %s codec: %s', endings, path)
            return codec_class

    return NoCodec
