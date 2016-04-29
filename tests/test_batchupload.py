__author__ = 'loopingz'

from nuxeo.blob import BufferBlob
from test_nuxeo import NuxeoTest


class BatchUploadTest(NuxeoTest):

    def test_upload(self):
        batch = self._nuxeo.batch_upload()
        self.assertIsNotNone(batch)
        self.assertIsNone(batch._batchid)
        batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
        self.assertIsNotNone(batch._batchid)
        blob = batch.get_blobs()[0]
        self.assertEqual(blob.fileIdx, 0)
        self.assertEqual(blob.uploadType, 'normal')
        self.assertEqual(blob.uploaded, True)
        self.assertEqual(blob.uploadedSize, 4)

    def test_cancel(self):
        batch = self._nuxeo.batch_upload()
        self.assertIsNotNone(batch)
        self.assertIsNone(batch._batchid)
        batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
        self.assertIsNotNone(batch._batchid)
        batch.cancel()
        self.assertIsNone(batch._batchid)
