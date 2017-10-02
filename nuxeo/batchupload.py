# coding: utf-8
import re

import urllib2

from .blob import BatchBlob

__all__ = ['BatchUpload']


def safe_filename(name, replacement=u'-'):
    """Replace invalid character in candidate filename"""
    return re.sub(ur'(/|\\|\*|:|\||"|<|>|\?)', replacement, name)

"""
A BatchUpload represent a bucket on the Nuxeo Server that allows you to add binary to then do some operation on it
"""
class BatchUpload(object):

    def __init__(self, nuxeo):
        self._nuxeo = nuxeo
        self._path = 'upload/'
        self._batchid = None
        self._upload_index = 0
        self._compatibiliy_mode = False
        self._blobs = []

    def get_blobs(self):
        """Get blobs contained in this BatchUpload"""
        return self._blobs

    def fetch(self, index):
        """Fetch a specific blob

        :param index: Get specified index
        """
        path = self._get_path() + '/' + str(index)
        res = self._nuxeo.request(path)
        res['fileIdx'] = index
        return BatchBlob(self, res)

    def upload(self, blob):
        """Upload a new blob to the bucket
        See the BufferBlob or FileBlob

        :param blob: The blob to upload to this BatchUpload
        """
        if self._batchid is None:
            self._batchid = self._create_batchid()
        if self._compatibiliy_mode:
            return self._old_upload(blob)
        filename = safe_filename(blob.get_name())
        quoted_filename = urllib2.quote(filename.encode('utf-8'))
        path = self._get_path() + '/' + str(self._upload_index)
        headers = {'Cache-Control': 'no-cache', 'X-File-Name': quoted_filename, 'X-File-Size': blob.get_size(), 'X-File-Type': blob.get_mimetype(), 'Content-Length': blob.get_size()}
        res = self._nuxeo.request(path, method="POST", body=blob.get_data(), content_type=blob.get_mimetype(), extra_headers=headers, raw_body=True)
        res['name'] = filename
        blob = BatchBlob(self, res)
        self._blobs.append(blob)
        self._upload_index+=1
        return blob

    def _old_upload(self, blob):
        # headers.update({"X-Batch-Id": batch_id, "X-File-Idx": file_index})
        url = self._nuxeo.automation_url.encode('ascii') + self.batch_upload_url
        pass

    def compatibility_mode(self):
        return self._compatibiliy_mode

    def get_batch_id(self):
        return self._batchid

    def _get_path(self):
        return self._path + self._batchid

    def cancel(self):
        """
        Cancel a BatchUpload, cleaning the bucket on the server side
        """
        if (self._batchid is None):
            return
        if self._compatibiliy_mode:
            return
        self._nuxeo.request(self._get_path(), method="DELETE")
        self._batchid = None

    def _create_batchid(self):
        try:
            res = self._nuxeo.request(self._path, method="POST")
            return res['batchId']
        except Exception as e:
            log_details = self._log_details(e)
            if isinstance(log_details, tuple):
                status, code, message, _ = log_details
                if status == 404:
                    self._compatibiliy_mode = True
                if status == 500:
                    not_found_exceptions = ['com.sun.jersey.api.NotFoundException',
                                            'org.nuxeo.ecm.webengine.model.TypeNotFoundException']
                    for exception in not_found_exceptions:
                        if code == exception or exception in message:
                            self._compatibiliy_mode = True
            raise e