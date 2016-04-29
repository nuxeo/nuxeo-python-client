__author__ = 'loopingz'


from common import NuxeoTest
from urllib2 import HTTPError


class OperationTest(NuxeoTest):

    def setUp(self):
        super(OperationTest, self).setUp()
        try:
            doc = self._nuxeo.repository().fetch('/default-domain/workspaces')
            docs = self._nuxeo.repository().query({'pageProvider': 'CURRENT_DOC_CHILDREN', 'queryParams': [doc.uid]})
            for doc in docs['entries']:
                doc.delete()
        except Exception:
            pass

    def test_params_setter(self):
        operation = self._nuxeo.operation('Noop')
        operation.params({'param1': 'foo', 'param2': 'bar'})
        self.assertEqual(operation._params['param1'],'foo')
        self.assertEqual(operation._params['param2'],'bar')
        operation.params({'param3': 'plop'})
        operation.params({'param1': 'bar'})
        self.assertEqual(operation._params['param1'],'bar')
        self.assertEqual(operation._params['param2'],'bar')
        self.assertEqual(operation._params['param3'],'plop')

    def test_document_fetch_by_property_params_validation(self):
        operation = self._nuxeo.operation('Document.FetchByProperty')
        # Missing mandatory params
        operation.params({'property': 'dc:title'})
        with self.assertRaises(ValueError):
            operation.execute()

    def test_document_fetch_by_property(self):
        operation = self._nuxeo.operation('Document.FetchByProperty')
        operation.params({'property': 'dc:title', 'values': 'Workspaces'})
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'documents')
        self.assertEquals(len(res['entries']), 1)
        self.assertEquals(res['entries'][0]['properties']['dc:title'], 'Workspaces')

    def test_document_get_child(self):
        operation = self._nuxeo.operation('Document.GetChild')
        operation.params({'name': 'workspaces'})
        operation.input('/default-domain')
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'document')
        self.assertEquals(res['properties']['dc:title'], 'Workspaces')

    def test_document_get_child_unknown(self):
        operation = self._nuxeo.operation('Document.GetChild')
        operation.params({'name': 'Workspaces'})
        operation.input('/default-domain')
        with self.assertRaises(HTTPError) as ex:
            operation.execute()
        self.assertEqual(ex.exception.code, 404)

    def test_document_list_update(self):
        # TODO Waiting for the repository object
        WS_ROOT_PATH = '/default-domain/workspaces';
        WS_JS_TEST_1_NAME = 'ws-js-tests1';
        WS_JS_TEST_2_NAME = 'ws-js-tests2';
        WS_JS_TESTS_1_PATH = WS_ROOT_PATH + '/' + WS_JS_TEST_1_NAME;
        WS_JS_TESTS_2_PATH = WS_ROOT_PATH + '/' + WS_JS_TEST_2_NAME;
        newDoc1 = {
          'name': WS_JS_TEST_1_NAME,
          'type': 'Workspace',
          'properties': {
            'dc:title': WS_JS_TEST_1_NAME,
          },
        }
        newDoc2 = {
          'name': WS_JS_TEST_2_NAME,
          'type': 'Workspace',
          'properties': {
            'dc:title': WS_JS_TEST_2_NAME,
          },
        }
        doc1 = self._nuxeo.repository().create(WS_ROOT_PATH, newDoc1)
        doc2 = self._nuxeo.repository().create(WS_ROOT_PATH, newDoc2)
        operation = self._nuxeo.operation('Document.Update')
        operation.params({'properties': {'dc:description':'sample description'}})
        operation.input([doc1.path, doc2.path])
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'documents')
        self.assertEquals(len(res['entries']), 2)
        self.assertEquals(res['entries'][0]['path'], doc1.path)
        self.assertEquals(res['entries'][0]['properties']['dc:description'], 'sample description')
        self.assertEquals(res['entries'][1]['path'], doc2.path)
        self.assertEquals(res['entries'][1]['properties']['dc:description'], 'sample description')
        doc1.delete()
        doc2.delete()