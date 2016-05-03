__author__ = 'loopingz'


from common import NuxeoTest
from nuxeo.document import Document
from urllib2 import HTTPError
from nuxeo.blob import BufferBlob

class RepositoryTest(NuxeoTest):
    WS_ROOT_PATH = '/default-domain/workspaces';
    WS_PYTHON_TEST_NAME = 'ws-python-tests';
    WS_PYTHON_TESTS_PATH = WS_ROOT_PATH + "/" + WS_PYTHON_TEST_NAME;

    def setUp(self):
        super(RepositoryTest, self).setUp()
        self._repository = self._nuxeo.repository(schemas=['dublincore'])
        try:
            root = self._repository.fetch(RepositoryTest.WS_PYTHON_TESTS_PATH)
            root.delete()
        except Exception as e:
            pass

    def test_fetch_root(self):
        root = self._repository.fetch('/')
        self.assertIsNotNone(root)
        self.assertTrue(isinstance(root, Document))

    def test_fetch_non_existing(self):
        with self.assertRaises(HTTPError) as ex:
            root = self._repository.fetch('/zone51')
        self.assertEqual(ex.exception.code, 404)

    def test_create_doc_and_delete(self):
        newDoc = {
            'name': RepositoryTest.WS_PYTHON_TEST_NAME,
            'type': 'Workspace',
            'properties': {
              'dc:title': 'foo',
            }
        }
        doc = self._repository.create(RepositoryTest.WS_ROOT_PATH, newDoc)
        self.assertIsNotNone(doc)
        self.assertTrue(isinstance(doc, Document))
        self.assertEqual(doc.path, RepositoryTest.WS_PYTHON_TESTS_PATH)
        self.assertEqual(doc.type, 'Workspace')
        self.assertEqual(doc.properties['dc:title'], 'foo')
        doc.delete()
        with self.assertRaises(HTTPError) as ex:
            root = self._repository.fetch(RepositoryTest.WS_PYTHON_TESTS_PATH)
        self.assertEqual(ex.exception.code, 404)


    def test_update_doc_and_delete(self):
        newDoc = {
            'name': RepositoryTest.WS_PYTHON_TEST_NAME,
            'type': 'Workspace',
            'properties': {
              'dc:title': 'foo',
            }
        }
        doc = self._repository.create(RepositoryTest.WS_ROOT_PATH, newDoc)
        uid = doc.uid
        path = doc.path
        self.assertIsNotNone(doc)
        doc.set({'dc:title': 'bar'})
        doc.save()
        doc = self._repository.fetch(RepositoryTest.WS_PYTHON_TESTS_PATH)
        self.assertTrue(isinstance(doc, Document))
        self.assertEqual(doc.uid, uid)
        self.assertEqual(doc.path, path)
        self.assertEqual(doc.properties['dc:title'], 'bar')
        doc.delete()

    def test_query(self):
        docs = self._repository.query({'query': 'SELECT * FROM Document WHERE ecm:primaryType = \'Domain\''})
        self.assertEqual(docs['numberOfPages'], 1)
        self.assertEqual(docs['resultsCount'], 1)
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 0)
        self.assertEqual(len(docs['entries']), 1)
        self.assertTrue(isinstance(docs['entries'][0], Document))

    def test_page_provider(self):
        doc = self._repository.fetch('/default-domain')
        docs = self._repository.query({'pageProvider': 'CURRENT_DOC_CHILDREN', 'queryParams': [doc.uid]})
        self.assertEqual(docs['numberOfPages'], 1)
        self.assertEqual(docs['resultsCount'], 3)
        self.assertEqual(docs['currentPageSize'], 3)
        self.assertEqual(docs['currentPageIndex'], 0)
        self.assertEqual(len(docs['entries']), 3)

    def test_page_provider_pagination(self):
        doc = self._repository.fetch('/default-domain')
        docs = self._repository.query({'pageProvider': 'document_content', 'queryParams': [doc.uid], 'pageSize': 1, 'currentPageIndex': 0, 'sortBy': 'dc:title', 'sortOrder': 'asc'})
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 0)
        self.assertEqual(docs['isNextPageAvailable'], True)
        self.assertEqual(len(docs['entries']), 1)
        self.assertTrue(isinstance(docs['entries'][0], Document))
        self.assertTrue(docs['entries'][0].title, 'Section')
        docs = self._repository.query({'pageProvider': 'document_content', 'queryParams': [doc.uid], 'pageSize': 1, 'currentPageIndex': 1, 'sortBy': 'dc:title', 'sortOrder': 'asc'})
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 1)
        self.assertEqual(docs['isNextPageAvailable'], True)
        self.assertEqual(len(docs['entries']), 1)
        self.assertTrue(isinstance(docs['entries'][0], Document))
        self.assertTrue(docs['entries'][0].title, 'Templates')
        docs = self._repository.query({'pageProvider': 'document_content', 'queryParams': [doc.uid], 'pageSize': 1, 'currentPageIndex': 2, 'sortBy': 'dc:title', 'sortOrder': 'asc'})
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 2)
        self.assertEqual(docs['isNextPageAvailable'], False)
        self.assertEqual(len(docs['entries']), 1)
        self.assertTrue(isinstance(docs['entries'][0], Document))
        self.assertTrue(docs['entries'][0].title, 'Workspaces')


    def _create_blob_file(self):
        newDoc = {
            'name': RepositoryTest.WS_PYTHON_TEST_NAME,
            'type': 'File',
            'properties': {
              'dc:title': 'bar.txt',
            }
        }
        doc = self._repository.create(RepositoryTest.WS_ROOT_PATH, newDoc)
        self.assertIsNotNone(doc)
        self.assertTrue(isinstance(doc, Document))
        self.assertEqual(doc.path, RepositoryTest.WS_PYTHON_TESTS_PATH)
        self.assertEqual(doc.type, 'File')
        self.assertEqual(doc.properties['dc:title'], 'bar.txt')
        blob = BufferBlob("foo", "foo.txt", "text/plain")
        blob = self._nuxeo.batch_upload().upload(blob)
        doc.properties["file:content"] = blob
        doc.save()
        #doc.refresh()
        #self.assertEqual(doc.properties["file:content"]["name"], "foo.txt")
        #self.assertEqual(doc.properties["file:content"]["length"], 3)
        #self.assertEqual(doc.properties["file:content"]["mime-type"], "text/plain")
        return doc

    def test_create_doc_and_convert(self):
        doc = self._create_blob_file()
        res = doc.convert({'format': 'html'})
        self.assertTrue('<html>' in res)
        self.assertTrue('foo' in res)
        doc.delete()

    def test_convert_given_converter(self):
        doc = self._create_blob_file()
        res = doc.convert({'converter': 'office2html'})
        self.assertTrue('<html>' in res)
        self.assertTrue('foo' in res)
        doc.delete()

    def test_convert_given_converter(self):
        doc = self._create_blob_file()
        res = doc.convert({'converter': 'office2html'})
        self.assertTrue('<html>' in res)
        self.assertTrue('foo' in res)
        doc.delete()

    def test_convert_xpath(self):
        doc = self._create_blob_file()
        res = doc.convert({ 'xpath': 'file:content', 'type': 'text/html' })
        self.assertTrue('<html>' in res)
        self.assertTrue('foo' in res)
        doc.delete()

    def test_fetch_renditions(self):
        doc = self._create_blob_file()
        res = doc.fetch_renditions()
        print res
        self.assertTrue('thumbnail' in res)
        self.assertTrue('xmlExport' in res)
        self.assertTrue('zipExport' in res)
        doc.delete()

    def test_fetch_rendition(self):
        doc = self._create_blob_file()
        res = doc.fetch_rendition('xmlExport')
        self.assertTrue('<?xml version="1.0" encoding="UTF-8"?>' in res)
        self.assertTrue(('<path>'+RepositoryTest.WS_PYTHON_TESTS_PATH[1:]+'</path>') in res)
        doc.delete()
