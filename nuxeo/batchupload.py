# coding: utf-8
from __future__ import unicode_literals

import re
import urllib2

from .blob import BatchBlob, FileBlob
from .exceptions import InvalidBatchException

__all__ = ('BatchUpload',)


def safe_filename(name, replacement='-'):
    """ Replace invalid character in candidate filename. """
    return re.sub(r'([/\\*:|"<>?])', replacement, name)


class BatchUpload(object):
    """
    A BatchUpload represent a bucket on the Nuxeo Server that allows
    you to add binary to then do some operation on it.
    """

    def __init__(self, nuxeo):
        self._nuxeo = nuxeo
        self._path = 'upload/'
        self.batchid = None
        self._upload_index = 0
        self.blobs = []

    def cancel(self):
        """ Cancel a BatchUpload, cleaning the bucket on the server side. """

        if self.batchid is None:
            return

        self._nuxeo.request(self._get_path(), method='DELETE')
        self.batchid = None

    def fetch(self, index):
        """
        Fetch a specific blob.

        :param index: Get specified index.
        """
        if self.batchid is None:
            raise InvalidBatchException('Cannot fetch blob for inexistant/deleted batch.')
        path = self._get_path() + '/' + str(index)
        res = self._nuxeo.request(path)
        res['fileIdx'] = index
        return BatchBlob(self, res)

    def get_batch_id(self):
        return self.batchid

    def upload(self, blob):
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
        blob = BatchBlob(self, res)
        self.blobs.append(blob)
        self._upload_index += 1
        return blob

    def _create_batchid(self):
        return self._nuxeo.request(self._path, method='POST')['batchId']

    def _get_path(self):
        return self._path + self.batchid
