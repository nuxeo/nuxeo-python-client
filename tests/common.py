__author__ = 'loopingz'
from unittest import TestCase
from nuxeo.nuxeo import Nuxeo

class NuxeoTest(TestCase):

    WS_ROOT_PATH = '/default-domain/workspaces';
    WS_PYTHON_TEST_NAME = 'ws-python-tests';
    WS_PYTHON_TESTS_PATH = WS_ROOT_PATH + "/" + WS_PYTHON_TEST_NAME;

    def setUp(self):
        self._nuxeo = Nuxeo("http://localhost:8080/nuxeo", auth={'username': 'Administrator', 'password': 'Administrator'})
        self._repository = self._nuxeo.repository(schemas=['dublincore'])

    def _clean_root(self):
        try:
            root = self._repository.fetch(NuxeoTest.WS_PYTHON_TESTS_PATH)
            root.delete()
        except Exception as e:
            pass

    def _create_blob_file(self):
        from nuxeo.blob import BufferBlob
        from nuxeo.document import Document
        newDoc = {
            'name': NuxeoTest.WS_PYTHON_TEST_NAME,
            'type': 'File',
            'properties': {
              'dc:title': 'bar.txt',
            }
        }
        doc = self._repository.create(NuxeoTest.WS_ROOT_PATH, newDoc)
        self.assertIsNotNone(doc)
        self.assertTrue(isinstance(doc, Document))
        self.assertEqual(doc.path, NuxeoTest.WS_PYTHON_TESTS_PATH)
        self.assertEqual(doc.type, 'File')
        self.assertEqual(doc.properties['dc:title'], 'bar.txt')
        blob = BufferBlob("foo", "foo.txt", "text/plain")
        blob = self._nuxeo.batch_upload().upload(blob)
        doc.properties["file:content"] = blob
        doc.save()
        return doc