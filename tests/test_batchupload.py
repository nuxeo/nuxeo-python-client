__author__ = 'loopingz'

from nuxeo.blob import BufferBlob
from test_nuxeo import NuxeoTest


class BatchUploadTest(NuxeoTest):

    def setUp(self):
        super(BatchUploadTest, self).setUp()
        self.batch = self._nuxeo.batch_upload()
        self.assertIsNotNone(self.batch)
        self.assertIsNone(self.batch._batchid)
        self.batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
        self.assertIsNotNone(self.batch._batchid)

    def test_upload(self):
        blob = self.batch.get_blobs()[0]
        self.assertEqual(blob.fileIdx, 0)
        self.assertEqual(blob.uploadType, 'normal')
        self.assertEqual(blob.uploaded, True)
        self.assertEqual(blob.uploadedSize, 4)

    def test_cancel(self):
        self.batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
        self.assertIsNotNone(self.batch._batchid)
        self.batch.cancel()
        self.assertIsNone(self.batch._batchid)

    def test_fetch(self):
        blob = self.batch.fetch(0)
        print blob
