# coding: utf-8
from __future__ import unicode_literals

from nuxeo.blob import BufferBlob
from test_nuxeo import NuxeoTest


class BatchUploadTest(NuxeoTest):

    def setUp(self):
        super(BatchUploadTest, self).setUp()
        self.batch = self.nuxeo.batch_upload()
        self.assertIsNotNone(self.batch)
        self.assertIsNone(self.batch._batchid)
        self.upload = self.batch.upload(
            BufferBlob('data', 'Test.txt', 'text/plain'))
        self.assertIsNotNone(self.batch._batchid)

    def test_upload(self):
        blob = self.batch.blobs[0]
        self.assertEqual(blob.fileIdx, 0)
        self.assertEqual(blob.uploadType, 'normal')
        self.assertIs(blob.uploaded, True)
        self.assertEqual(blob.uploadedSize, 4)

    def test_cancel(self):
        self.batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
        self.assertIsNotNone(self.batch._batchid)
        self.batch.cancel()
        self.assertIsNone(self.batch._batchid)

    def test_fetch(self):
        blob = self.batch.fetch(0)
        self.assertEqual(blob.fileIdx, 0)
        self.assertEqual(blob.uploadType, 'normal')
        self.assertEqual(blob.get_name(), 'Test.txt')
        self.assertEqual(blob.get_size(), 4)

    def test_operation(self):
        new_doc = {
            'name': 'Document',
            'type': 'File',
            'properties': {
                'dc:title': 'foo',
            }
        }
        doc = self.nuxeo.repository(schemas=['dublincore', 'file']).create(
            NuxeoTest.WS_ROOT_PATH, new_doc)
        try:
            self.assertIsNone(doc.properties['file:content'])
            operation = self.nuxeo.operation('Blob.AttachOnDocument')
            operation.params({'document': NuxeoTest.WS_ROOT_PATH + '/Document'})
            operation.input(self.upload)
            operation.execute()
            doc = self.nuxeo.repository(schemas=['dublincore', 'file']).fetch(
                NuxeoTest.WS_ROOT_PATH + '/Document')
            self.assertIsNotNone(doc.properties['file:content'])
            self.assertEqual(doc.fetch_blob(), 'data')
        finally:
            doc.delete()
