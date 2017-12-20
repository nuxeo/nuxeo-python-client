# coding: utf-8
from __future__ import unicode_literals

import mimetypes
import os
import sys
from io import StringIO

from .compat import text

try:
    from typing import Any, Dict, IO, Optional, Text, Union
except ImportError:
    pass

__all__ = ('BlobInfo', 'Blob', 'BufferBlob', 'FileBlob')


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


def guess_mime_type(filename):
    # type: (Text) -> Text
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if sys.platform == 'win32':
            # Patch bad Windows MIME types
            # See http://bugs.python.org/issue15207 and NXP-11660
            mime_type = WIN32_PATCHED_MIME_TYPES.get(mime_type, mime_type)
        return mime_type

    return 'application/octet-stream'


class Blob(object):
    """
    Abstract representation of a Blob.
    You should use :class:`BufferBlob` or :class:`FileBlob`.
    """

    def __init__(self):
        # type: () -> None
        self._name = None
        self._size = 0
        self._data = ''
        self._mimetype = 'application/octet-stream'

    def get_data(self):
        # type: () -> Union[IO[bytes], StringIO, Text]
        """ Data. """
        return self._data

    def get_mimetype(self):
        # type: () -> Text
        """ Mimetype for the content. """
        return self._mimetype

    def get_name(self):
        # type: () -> Text
        """ Return the name to use. """
        return self._name

    def get_size(self):
        # type: () -> int
        """ Size in bytes. """
        return self._size


class BlobInfo(object):
    """ Contains info about an uploaded Blob. """

    def __init__(self, service, obj):
        # type: (BatchUpload, Dict[Text, Any]) -> None
        self.service = service
        self.uploaded = obj.get('uploaded', 'true') == 'true'
        self.uploadType = obj['uploadType']
        self.name = obj['name']
        self.size = int(obj.get('size', 0))
        self.uploadedSize = int(obj.get('uploadedSize', self.size))
        self.fileIdx = int(obj['fileIdx'])

    def get_batch_id(self):
        # type: () -> Text
        return self.service.get_batch_id()

    def to_json(self):
        # type: () -> Dict[Text, Text]
        return {
            'upload-batch': self.get_batch_id(),
            'upload-fileId': text(self.fileIdx),
        }


class BufferBlob(Blob):
    """ InMemory content to upload to Nuxeo. """

    def __init__(self, buf, name, mimetype='application/octet-stream'):
        # type: (Text, Text, Text) -> None
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
        # type: () -> StringIO
        return StringIO(self._buffer)

    def get_size(self):
        # type: () -> int
        return len(self._buffer)


class FileBlob(Blob):
    """ Represent a File as Blob for future upload. """

    def __init__(self, path, mimetype=None):
        # type: (Text, Optional[Text]) -> None
        """
        :param path: To the file.
        :param mimetype: If not specified client will try to guess.
        """

        super(FileBlob, self).__init__()
        self._path = path
        self._name = os.path.basename(self._path)
        self._size = os.path.getsize(self._path)
        self._mimetype = mimetype or guess_mime_type(path)

    def get_data(self):
        # type: () -> IO[bytes]
        """ Request data. """

        return open(self._path, 'rb')
