__author__ = 'loopingz'


from test_nuxeo import NuxeoTest
from urllib2 import HTTPError


class OperationTest(NuxeoTest):

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
        operation = self._nuxeo.operation('Document.Update')
        operation.params({'name': 'workspaces'})
        operation.input('/default-domain')
        res = operation.execute()
        self.assertEquals(res['entity-type'], 'document')
        self.assertEquals(res['properties']['dc:title'], 'Workspaces')