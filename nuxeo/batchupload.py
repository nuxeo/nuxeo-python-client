# coding: utf-8
from __future__ import unicode_literals

import re
import urllib2

from typing import Text

from .blob import Blob, BlobInfo, FileBlob
from .exceptions import InvalidBatchException

__all__ = ('BatchUpload',)


def safe_filename(name, replacement='-'):
    # type: (Text, Text) -> Text
    """ Replace invalid character in candidate filename. """
    return re.sub(r'([/\\*:|"<>?])', replacement, name)


class BatchUpload(object):
    """
    A BatchUpload represent a bucket on the Nuxeo Server that allows
    you to add binary to then do some operation on it.
    """

    def __init__(self, nuxeo):
        # type: (Nuxeo) -> None
        self._nuxeo = nuxeo
        self._path = 'upload/'
        self.batchid = None
        self._upload_index = 0
        self.blobs = []

    def cancel(self):
        # type: () -> None
        """ Cancel a BatchUpload, cleaning the bucket on the server side. """

        if self.batchid is None:
            return

        self._nuxeo.request(self._get_path(), method='DELETE')
        self.batchid = None

    def fetch(self, index):
        # type: (int) -> BlobInfo
        """
        Fetch a specific blob.

        :param index: Get specified index.
        """
        if self.batchid is None:
            raise InvalidBatchException('Cannot fetch blob for inexistant/deleted batch.')
        path = self._get_path() + '/' + str(index)
        res = self._nuxeo.request(path)
        res['fileIdx'] = index
        return BlobInfo(self, res)

    def get_batch_id(self):
        # type: () -> Text
        return self.batchid

    def upload(self, blob):
        # type: (Blob) -> BlobInfo
        """
        Upload a new blob to the bucket.
        See the :class:`BufferBlob` or :class:`FileBlob`.

        :param blob: The blob to upload to this BatchUpload.
        """

        if self.batchid is None:
            self.batchid = self._create_batchid()
        filename = safe_filename(blob.get_name())
        quoted_filename = urllib2.quote(filename.encode('utf-8'))
        path = self._get_path() + '/' + str(self._upload_index)
        headers = {
            'Cache-Control': 'no-cache',
            'X-File-Name': quoted_filename,
            'X-File-Size': str(blob.get_size()),
            'X-File-Type': blob.get_mimetype(),
            'Content-Length': str(blob.get_size()),
        }
        data = blob.get_data()
        try:
            res = self._nuxeo.request(
                path,
                method='POST',
                body=data,
                content_type=blob.get_mimetype(),
                extra_headers=headers,
                raw_body=True,
            )
        finally:
            if isinstance(blob, FileBlob):
                data.close()
        res['name'] = filename
        blob = BlobInfo(self, res)
        self.blobs.append(blob)
        self._upload_index += 1
        return blob

    def _create_batchid(self):
        # type: () -> Text
        return self._nuxeo.request(self._path, method='POST')['batchId']

    def _get_path(self):
        # type: () -> Text
        return self._path + self.batchid
