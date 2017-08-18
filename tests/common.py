# coding: utf-8
import os
import socket
import unittest
import urllib2

from nuxeo.blob import BufferBlob
from nuxeo.document import Document
from nuxeo.nuxeo import Nuxeo


class NuxeoTest(unittest.TestCase):

    WS_ROOT_PATH = '/default-domain/workspaces'
    WS_PYTHON_TEST_NAME = 'ws-python-tests'
    WS_PYTHON_TESTS_PATH = WS_ROOT_PATH + '/' + WS_PYTHON_TEST_NAME

    def setUp(self):
        self.base_url = os.environ.get(
            'NXDRIVE_TEST_NUXEO_URL', 'http://localhost:8080/nuxeo')
        auth = {'username': 'Administrator', 'password': 'Administrator'}
        self.nuxeo = Nuxeo(base_url=self.base_url, auth=auth)
        self.repository = self.nuxeo.repository(schemas=['dublincore'])

    def _clean_root(self):
        try:
            root = self.repository.fetch(self.WS_PYTHON_TESTS_PATH)
            root.delete()
        except (urllib2.HTTPError, socket.timeout):
            pass

    def _create_blob_file(self):
        doc = {
            'name': self.WS_PYTHON_TEST_NAME,
            'type': 'File',
            'properties': {
              'dc:title': 'bar.txt',
            },
        }
        doc = self.repository.create(self.WS_ROOT_PATH, doc)
        self.assertIsNotNone(doc)
        self.assertTrue(isinstance(doc, Document))
        self.assertEqual(doc.path, self.WS_PYTHON_TESTS_PATH)
        self.assertEqual(doc.type, 'File')
        self.assertEqual(doc.properties['dc:title'], 'bar.txt')
        blob = BufferBlob('foo', 'foo.txt', 'text/plain')
        blob = self.nuxeo.batch_upload().upload(blob)
        doc.properties['file:content'] = blob
        doc.save()
        return doc
