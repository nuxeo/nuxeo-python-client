# coding: utf-8
from __future__ import unicode_literals

import mimetypes
import os
import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

__all__ = [
    'Blob',
    'BatchBlob',
    'BufferBlob',
    'FileBlob',
]


FILE_BUFFER_SIZE = 1024 ** 2

WIN32_PATCHED_MIME_TYPES = {
    'image/pjpeg': 'image/jpeg',
    'image/x-png': 'image/png',
    'image/bmp': 'image/x-ms-bmp',
    'audio/x-mpg': 'audio/mpeg',
    'video/x-mpeg2a': 'video/mpeg',
    'application/x-javascript': 'application/javascript',
    'application/x-msexcel': 'application/vnd.ms-excel',
    'application/x-mspowerpoint': 'application/vnd.ms-powerpoint',
    'application/x-mspowerpoint.12':
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}


def _patch_win32_mime_type(mime_type):
    patched_mime_type = WIN32_PATCHED_MIME_TYPES.get(mime_type)
    return patched_mime_type if patched_mime_type else mime_type


def guess_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if sys.platform == 'win32':
            # Patch bad Windows MIME types
            # See https://jira.nuxeo.com/browse/NXP-11660
            # and http://bugs.python.org/issue15207
            mime_type = _patch_win32_mime_type(mime_type)
        return mime_type
    
    return 'application/octet-stream'


class Blob(object):
    """
    Abstract representation of a Blob.
    You should use :class:`BufferBlob` or :class:`FileBlob`.
    """

    def __init__(self):
        self._name = None
        self._size = 0
        self._data = ''
        self._mimetype = 'application/octet-stream'

    def get_name(self):
        """ Return the name to use. """
        return self._name

    def get_size(self):
        """ Size in bytes. """
        return self._size

    def get_mimetype(self):
        """ Mimetype for the content. """
        return self._mimetype

    def get_data(self):
        """ Data. """
        return self._data


class BatchBlob(Blob):
    """ Representation of an already uploaded Blob. """

    def __init__(self, service, obj):
        self._service = service
        if 'uploaded' in obj:
            self.uploaded = obj['uploaded'] == "true"
        else:
            self.uploaded = True
        self.uploadType = obj['uploadType']
        self._name = obj['name']
        if 'size' in obj:
            self._size = int(obj['size'])
        else:
            self._size = 0
        if 'uploadedSize' in obj:
            self.uploadedSize = int(obj['uploadedSize'])
        else:
            self.uploadedSize = self._size
        self.fileIdx = int(obj['fileIdx'])

    def to_json(self):
        return {
            'upload-batch': self.get_batch_id(),
            'upload-fileId': str(self.fileIdx),
        }

    def get_batch_id(self):
        return self._service.get_batch_id()


class BufferBlob(Blob):
    """ InMemory content to upload to Nuxeo. """

    def __init__(self, buf, name, mimetype='application/octect-stream'):
        """
        :param buf: Content to upload to Nuxeo.
        :param name: Name to give to the file created on the server.
        :param mimetype: Mimetype of the content.
        """

        super(BufferBlob, self).__init__()
        self._name = name
        self._mimetype = mimetype
        self._buffer = buf

    def get_data(self):
        return StringIO(self._buffer)

    def get_size(self):
        return len(self._buffer)


class FileBlob(Blob):
    """ Represent a File as Blob for future upload. """

    def __init__(self, path, mimetype=None):
        """
        :param path: To the file.
        :param mimetype: If not specified client will try to guess.
        """

        super(FileBlob, self).__init__()
        self._path = path
        self._name = os.path.basename(self._path)
        self._size = os.path.getsize(self._path)
        if mimetype is None:
            self._mimetype = guess_mime_type(path)
        else:
            self._mimetype = mimetype

    def get_upload_buffer(self, input_file):
        if sys.platform != 'win32':
            return os.fstatvfs(input_file.fileno()).f_bsize

        return FILE_BUFFER_SIZE

    def _read_data(self, file_object, buffer_size):
        while 'processing data':
            # Check if synchronization thread was suspended
            r = file_object.read(buffer_size)
            if not r:
                break
            yield r

    def get_data(self):
        """ Request data. """

        input_file = open(self._path, 'rb')
        # Use file system block size if available for streaming buffer
        fs_block_size = self.get_upload_buffer(input_file)
        return self._read_data(input_file, fs_block_size)
