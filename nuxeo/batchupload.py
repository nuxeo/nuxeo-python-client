# coding: utf-8
from __future__ import unicode_literals

import re

import urllib2

from .blob import BatchBlob

__all__ = ['BatchUpload']


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
        self._batchid = None
        self._upload_index = 0
        self.blobs = []

    def fetch(self, index):
        """
        Fetch a specific blob.

        :param index: Get specified index.
        """

        path = self._get_path() + '/' + str(index)
        res = self._nuxeo.request(path)
        res['fileIdx'] = index
        return BatchBlob(self, res)

    def upload(self, blob):
        """
        Upload a new blob to the bucket.
        See the :class:`BufferBlob` or :class:`FileBlob`.

        :param blob: The blob to upload to this BatchUpload.
        """

        if self._batchid is None:
            self._batchid = self._create_batchid()
        filename = safe_filename(blob.get_name())
        quoted_filename = urllib2.quote(filename.encode('utf-8'))
        path = self._get_path() + '/' + str(self._upload_index)
        headers = {
            'Cache-Control': 'no-cache',
            'X-File-Name': quoted_filename,
            'X-File-Size': blob.get_size(),
            'X-File-Type': blob.get_mimetype(),
            'Content-Length': blob.get_size(),
        }
        res = self._nuxeo.request(
            path,
            method='POST',
            body=blob.get_data(),
            content_type=blob.get_mimetype(),
            extra_headers=headers,
            raw_body=True,
        )
        res['name'] = filename
        blob = BatchBlob(self, res)
        self.blobs.append(blob)
        self._upload_index += 1
        return blob

    def get_batch_id(self):
        return self._batchid

    def _get_path(self):
        return self._path + self._batchid

    def cancel(self):
        """ Cancel a BatchUpload, cleaning the bucket on the server side. """

        if self._batchid is None:
            return

        self._nuxeo.request(self._get_path(), method='DELETE')
        self._batchid = None

    def _create_batchid(self):
        return self._nuxeo.request(self._path, method='POST')['batchId']
