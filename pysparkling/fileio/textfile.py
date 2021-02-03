from io import BytesIO, StringIO, TextIOWrapper
import logging

from . import codec
from .file import File
from .fs.file_system import FileSystem

log = logging.getLogger(__name__)


class TextFile(File):
    """Derived from :class:`File`.

    :param file_name: Any text file name.
    """

    def load(self, encoding='utf8', encoding_errors='ignore'):  # pylint: disable=arguments-differ
        """Load the data from a file.

        :param str encoding: The character encoding of the file.
        :param str encoding_errors: How to handle encoding errors.
        :rtype: io.StringIO
        """
        # pylint: disable=comparison-with-callable
        if isinstance(self.codec, codec.NoCodec) and \
           self.fs.load_text != FileSystem.load_text:
            stream = self.fs.load_text(encoding, encoding_errors)
        else:
            stream = self.fs.load()
            stream = self.codec.decompress(stream)
            stream = TextIOWrapper(stream, encoding, encoding_errors)
        return stream

    def dump(self, stream=None, encoding='utf8', encoding_errors='ignore'):  # pylint: disable=arguments-differ
        """Writes a stream to a file.

        :param stream:
            An ``io.StringIO`` instance. A ``str`` is also possible and
            get converted to ``io.StringIO``.

        :param encoding: (optional)
            The character encoding of the file.

        :rtype: TextFile
        """
        if stream is None:
            stream = StringIO()

        if isinstance(stream, str):
            stream = StringIO(stream)

        stream = self.codec.compress(
            BytesIO(stream.read().encode(encoding, encoding_errors))
        )
        self.fs.dump(stream)

        return self
