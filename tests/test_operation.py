# coding: utf-8
from __future__ import unicode_literals

from urllib2 import HTTPError

from .common import NuxeoTest


class OperationTest(NuxeoTest):

    def setUp(self):
        super(OperationTest, self).setUp()
        try:
            doc = self.nuxeo.repository().fetch('/default-domain/workspaces')
            params = {'pageProvider': 'CURRENT_DOC_CHILDREN',
                      'queryParams': [doc.uid]}
            docs = self.nuxeo.repository().query(params)
            for doc in docs['entries']:
                doc.delete()
        except:
            pass

    def test_params_setter(self):
        operation = self.nuxeo.operation('Noop')
        operation.params({'param1': 'foo', 'param2': 'bar'})
        self.assertEqual(operation._params['param1'], 'foo')
        self.assertEqual(operation._params['param2'], 'bar')
        operation.params({'param3': 'plop'})
        operation.params({'param1': 'bar'})
        self.assertEqual(operation._params['param1'], 'bar')
        self.assertEqual(operation._params['param2'], 'bar')
        self.assertEqual(operation._params['param3'], 'plop')

    def test_document_fetch_by_property_params_validation(self):
        """ Missing mandatory params. """
        operation = self.nuxeo.operation('Document.FetchByProperty')
        operation.params({'property': 'dc:title'})
        with self.assertRaises(ValueError):
            operation.execute()

    def test_document_fetch_by_property(self):
        operation = self.nuxeo.operation('Document.FetchByProperty')
        operation.params({'property': 'dc:title', 'values': 'Workspaces'})
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'documents')
        self.assertEquals(len(res['entries']), 1)
        self.assertEquals(res['entries'][0]['properties']['dc:title'],
                          'Workspaces')

    def test_document_get_child(self):
        operation = self.nuxeo.operation('Document.GetChild')
        operation.params({'name': 'workspaces'})
        operation.input('/default-domain')
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'document')
        self.assertEquals(res['properties']['dc:title'], 'Workspaces')

    def test_document_get_child_unknown(self):
        operation = self.nuxeo.operation('Document.GetChild')
        operation.params({'name': 'Workspaces'})
        operation.input('/default-domain')
        with self.assertRaises(HTTPError) as ex:
            operation.execute()
        self.assertEqual(ex.exception.code, 404)

    def test_document_list_update(self):
        # TODO Waiting for the repository object
        new_doc1 = {
            'name': 'ws-js-tests1',
            'type': 'Workspace',
            'properties': {
                'dc:title': 'ws-js-tests1',
            },
        }
        new_doc2 = {
            'name': 'ws-js-tests2',
            'type': 'Workspace',
            'properties': {
                'dc:title': 'ws-js-tests2',
            },
        }
        doc1 = self.nuxeo.repository().create(NuxeoTest.WS_ROOT_PATH, new_doc1)
        doc2 = self.nuxeo.repository().create(NuxeoTest.WS_ROOT_PATH, new_doc2)
        desc = 'sample description'
        operation = self.nuxeo.operation('Document.Update')
        operation.params({'properties': {'dc:description': desc}})
        operation.input([doc1.path, doc2.path])
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'documents')
        self.assertEquals(len(res['entries']), 2)
        self.assertEquals(res['entries'][0]['path'], doc1.path)
        self.assertEquals(res['entries'][0]['properties']['dc:description'], desc)
        self.assertEquals(res['entries'][1]['path'], doc2.path)
        self.assertEquals(res['entries'][1]['properties']['dc:description'], desc)
        doc1.delete()
        doc2.delete()
