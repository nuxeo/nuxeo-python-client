# coding: utf-8
from __future__ import unicode_literals

import operator
import sys
import urllib2

import pytest

from nuxeo.document import Document
from . import NuxeoTest


class TestRepository(NuxeoTest):

    def setUp(self):
        super(TestRepository, self).setUp()
        self._clean_root()

    def test_fetch_root(self):
        root = self.repository.fetch('/')
        self.assertIsNotNone(root)
        self.assertIsInstance(root, Document)

    def test_fetch_non_existing(self):
        with self.assertRaises(urllib2.HTTPError) as ex:
            self.repository.fetch('/zone51')
        self.assertEqual(ex.exception.code, 404)

    def test_create_doc_and_delete(self):
        new_doc = {
            'name': NuxeoTest.WS_PYTHON_TEST_NAME,
            'type': 'Workspace',
            'properties': {
              'dc:title': 'foo',
            }
        }
        doc = self.repository.create(NuxeoTest.WS_ROOT_PATH, new_doc)
        self.assertIsNotNone(doc)
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.path, NuxeoTest.WS_PYTHON_TESTS_PATH)
        self.assertEqual(doc.type, 'Workspace')
        self.assertEqual(doc.properties['dc:title'], 'foo')
        doc.delete()
        with self.assertRaises(urllib2.HTTPError) as ex:
            self.repository.fetch(NuxeoTest.WS_PYTHON_TESTS_PATH)
        self.assertEqual(ex.exception.code, 404)

    def test_create_doc_with_space_and_delete(self):
        """ NXPY-14: URLs should be quoted. """

        name = 'my domain'
        new_doc = {
            'name': name,
            'type': 'Workspace',
            'properties': {
                'dc:title': name.title(),
            }
        }
        doc = self.repository.create(NuxeoTest.WS_ROOT_PATH, new_doc)
        self.assertIsInstance(doc, Document)
        self.repository.fetch(NuxeoTest.WS_ROOT_PATH + '/' + name)
        doc.delete()

    def test_update_doc_and_delete(self):
        new_doc = {
            'name': NuxeoTest.WS_PYTHON_TEST_NAME,
            'type': 'Workspace',
            'properties': {
                'dc:title': 'foo',
            }
        }
        doc = self.repository.create(NuxeoTest.WS_ROOT_PATH, new_doc)
        uid = doc.uid
        path = doc.path
        self.assertIsNotNone(doc)
        doc.set({'dc:title': 'bar'})
        doc.save()
        doc = self.repository.fetch(NuxeoTest.WS_PYTHON_TESTS_PATH)
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.uid, uid)
        self.assertEqual(doc.path, path)
        self.assertEqual(doc.properties['dc:title'], 'bar')
        doc.delete()

    def test_query(self):
        docs = self.repository.query({'query': 'SELECT * FROM Document WHERE ecm:primaryType = \'Domain\''})
        self.assertEqual(docs['numberOfPages'], 1)
        self.assertEqual(docs['resultsCount'], 1)
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 0)
        self.assertEqual(len(docs['entries']), 1)
        self.assertIsInstance(docs['entries'][0], Document)

    def test_page_provider(self):
        doc = self.repository.fetch('/default-domain')
        docs = self.repository.query({'pageProvider': 'CURRENT_DOC_CHILDREN',
                                      'queryParams': [doc.uid]})
        self.assertEqual(docs['numberOfPages'], 1)
        self.assertEqual(docs['resultsCount'], 3)
        self.assertEqual(docs['currentPageSize'], 3)
        self.assertEqual(docs['currentPageIndex'], 0)
        self.assertEqual(len(docs['entries']), 3)

    def test_page_provider_pagination(self):
        doc = self.repository.fetch('/default-domain')
        docs = self.repository.query({'pageProvider': 'document_content',
                                      'queryParams': [doc.uid],
                                      'pageSize': 1,
                                      'currentPageIndex': 0,
                                      'sortBy': 'dc:title',
                                      'sortOrder': 'asc'})
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 0)
        self.assertIs(docs['isNextPageAvailable'], True)
        self.assertEqual(len(docs['entries']), 1)
        self.assertIsInstance(docs['entries'][0], Document)
        self.assertTrue(docs['entries'][0].title, 'Section')
        docs = self.repository.query({'pageProvider': 'document_content',
                                      'queryParams': [doc.uid],
                                      'pageSize': 1,
                                      'currentPageIndex': 1,
                                      'sortBy': 'dc:title',
                                      'sortOrder': 'asc'})
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 1)
        self.assertIs(docs['isNextPageAvailable'], True)
        self.assertEqual(len(docs['entries']), 1)
        self.assertIsInstance(docs['entries'][0], Document)
        self.assertTrue(docs['entries'][0].title, 'Templates')
        docs = self.repository.query({'pageProvider': 'document_content',
                                      'queryParams': [doc.uid],
                                      'pageSize': 1,
                                      'currentPageIndex': 2,
                                      'sortBy': 'dc:title',
                                      'sortOrder': 'asc'})
        self.assertEqual(docs['currentPageSize'], 1)
        self.assertEqual(docs['currentPageIndex'], 2)
        self.assertIs(docs['isNextPageAvailable'], False)
        self.assertEqual(len(docs['entries']), 1)
        self.assertIsInstance(docs['entries'][0], Document)
        self.assertTrue(docs['entries'][0].title, 'Workspaces')

    @pytest.mark.skipif(sys.platform == 'darwin',
                        reason='office2html is not on macOS')
    def test_convert(self):
        doc = self._create_blob_file()
        res = doc.convert({'format': 'html'})
        self.assertIn('<html>', res)
        self.assertIn('foo', res)
        doc.delete()

    @pytest.mark.skipif(sys.platform == 'darwin',
                        reason='office2html is not on macOS')
    def test_convert_given_converter(self):
        doc = self._create_blob_file()
        res = doc.convert({'converter': 'office2html'})
        self.assertIn('<html>', res)
        self.assertIn('foo', res)

    @pytest.mark.skipif(sys.platform == 'darwin',
                        reason='office2html is not on macOS')
    def test_convert_xpath(self):
        doc = self._create_blob_file()
        res = doc.convert({'xpath': 'file:content', 'type': 'text/html'})
        self.assertTrue('<html>' in res)
        self.assertTrue('foo' in res)

    def test_fetch_renditions(self):
        doc = self._create_blob_file()
        res = doc.fetch_renditions()
        self.assertIn('thumbnail', res)
        self.assertIn('xmlExport', res)
        self.assertIn('zipExport', res)

    def test_fetch_rendition(self):
        doc = self._create_blob_file()
        res = doc.fetch_rendition('xmlExport')
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', res)
        path = '<path>' + NuxeoTest.WS_PYTHON_TESTS_PATH[1:] + '</path>'
        self.assertIn(path, res)

    def test_fetch_blob(self):
        doc = self._create_blob_file()
        res = doc.fetch_blob()
        self.assertEqual(res, 'foo')

    def test_fetch_acls(self):
        doc = self._create_blob_file()
        acls = doc.fetch_acls()
        self.assertEqual(len(acls), 1)
        self.assertEqual(acls[0]['name'], 'inherited')
        aces = list(sorted(acls[0]['aces'], key=operator.itemgetter('id')))
        self.assertEqual(aces[0]['id'], 'Administrator:Everything:true:::')
        self.assertEqual(aces[1]['id'], 'members:Read:true:::')

    def test_add_remove_permission(self):
        doc = self._create_blob_file()
        doc.add_permission({'username': 'members', 'permission': 'Write'})
        acls = doc.fetch_acls()
        self.assertEqual(len(acls), 2)
        self.assertEqual(acls[0]['name'], 'local')
        self.assertEqual(acls[0]['aces'][0]['id'],
                         'members:Write:true:Administrator::')
        doc.remove_permission({'id': 'members:Write:true:Administrator::'})
        acls = doc.fetch_acls()
        self.assertEqual(len(acls), 1)
        self.assertEqual(acls[0]['name'], 'inherited')

    def test_has_permission(self):
        doc = self._create_blob_file()
        self.assertTrue(doc.has_permission('Write'))
        self.assertFalse(doc.has_permission('Foo'))

    def test_locking(self):
        doc = self._create_blob_file()
        status = doc.fetch_lock_status()
        self.assertEqual(status, {})
        self.assertFalse(doc.is_locked())
        doc.lock()
        status = doc.fetch_lock_status()
        self.assertEqual(status['lockOwner'], 'Administrator')
        self.assertIn('lockCreated', status)
        self.assertTrue(doc.is_locked())
        with self.assertRaises(urllib2.HTTPError):
            doc.lock()
        doc.unlock()
        self.assertFalse(doc.is_locked())
