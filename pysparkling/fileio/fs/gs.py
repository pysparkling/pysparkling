from __future__ import absolute_import

from fnmatch import fnmatch
import logging
from io import BytesIO, StringIO

from ...utils import Tokenizer
from .file_system import FileSystem
from ...exceptions import FileSystemNotSupported

log = logging.getLogger(__name__)

try:
    from gcloud import storage
except ImportError:
    storage = None


class GS(FileSystem):
    _clients = {}

    def __init__(self, file_name):
        if storage is None:
            raise FileSystemNotSupported(
                'Google Storage is not supported. Install "gcloud".'
            )

        super(GS, self).__init__(file_name)

        # obtain key
        t = Tokenizer(self.file_name)
        t.next('://')  # skip scheme
        project_name = t.next(':')
        bucket_name = t.next('/')
        blob_name = t.next()

        client = GS._get_client(project_name)
        bucket = client.get_bucket(bucket_name)
        self.blob = bucket.get_blob(blob_name)
        if not self.blob:
            self.blob = bucket.blob(blob_name)

    @staticmethod
    def _get_client(project_name):
        if project_name not in GS._clients:
            GS._clients[project_name] = storage.Client(project_name)
        return GS._clients[project_name]

    @staticmethod
    def resolve_filenames(expr):
        files = []

        t = Tokenizer(expr)
        scheme = t.next('://')
        project_name = t.next(':')
        bucket_name = t.next('/')
        prefix = t.next(['*', '?'])

        bucket = GS._get_client(project_name).get_bucket(bucket_name)
        expr = expr[len(scheme)+3+len(project_name)+1+len(bucket_name)+1:]
        for k in bucket.list_blobs(prefix=prefix):
            if fnmatch(k.name, expr) or fnmatch(k.name, expr + '/part*'):
                files.append('{0}://{1}:{2}/{3}'.format(
                    scheme,
                    project_name,
                    bucket_name,
                    k.name,
                ))
        return files

    def exists(self):
        t = Tokenizer(self.file_name)
        t.next('//')  # skip scheme
        project_name = t.next(':')
        bucket_name = t.next('/')
        blob_name = t.next()
        bucket = GS._get_client(project_name).get_bucket(bucket_name)
        return (bucket.get_blob(blob_name) or
                list(bucket.list_blobs(prefix=blob_name+'/')))

    def load(self):
        log.debug('Loading {0} with size {1}.'
                  ''.format(self.blob.name, self.blob.size))
        return BytesIO(self.blob.download_as_string())

    def load_text(self, encoding='utf8', encoding_errors='ignore'):
        log.debug('Loading {0} with size {1}.'
                  ''.format(self.blob.name, self.blob.size))
        return StringIO(
            self.blob.download_as_string().decode(
                encoding, encoding_errors
            )
        )

    def dump(self, stream):
        log.debug('Dumping to {0}.'.format(self.blob.name))
        self.blob.upload_from_string(stream.read())
        return self

    def make_public(self, recursive=False):
        self.blob.make_public(recursive)
        return self
