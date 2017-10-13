# coding: utf-8
from __future__ import unicode_literals

from test_nuxeo import NuxeoTest


class TestDocument(NuxeoTest):

    def test_document_create(self):
        operation = self.nuxeo.operation('Document.Create')
        operation.params({
            'type': 'File',
            'name': 'foo.txt',
            'properties': {'dc:title': 'foo.txt',
                           'dc:description': 'bar'}
        })
        operation.input('/')
        doc = operation.execute()
        self.assertEqual(doc['entity-type'], 'document')
        self.assertEqual(doc['type'], 'File')
        self.assertEqual(doc['title'], 'foo.txt')
        self.assertEqual(doc['properties']['dc:title'], 'foo.txt')
        self.assertEqual(doc['properties']['dc:description'], 'bar')
        self.repository.delete('/' + doc['title'])

    def test_document_create_properties_as_str(self):
        operation = self.nuxeo.operation('Document.Create')
        operation.params({
            'type': 'File',
            'name': 'foo.txt',
            'properties': 'dc:title=foo.txt\ndc:description=bar',
        })
        operation.input('/')
        doc = operation.execute()
        self.assertEqual(doc['entity-type'], 'document')
        self.assertEqual(doc['type'], 'File')
        self.assertEqual(doc['title'], 'foo.txt')
        self.assertEqual(doc['properties']['dc:title'], 'foo.txt')
        self.assertEqual(doc['properties']['dc:description'], 'bar')
        self.repository.delete('/' + doc['title'])
