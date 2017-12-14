# coding: utf-8
from __future__ import unicode_literals

from requests import HTTPError

import pytest


def test_document_fetch_by_property(server):
    operation = server.operation('Document.FetchByProperty')
    operation.params({'property': 'dc:title', 'values': 'Workspaces'})
    res = operation.execute()
    assert res['entity-type'] == 'documents'
    assert len(res['entries']) == 1
    assert res['entries'][0]['properties']['dc:title'] == 'Workspaces'


def test_document_fetch_by_property_params_validation(server):
    """ Missing mandatory params. """
    operation = server.operation('Document.FetchByProperty')
    operation.params({'property': 'dc:title'})
    with pytest.raises(ValueError):
        operation.execute(check_params=True)


def test_document_get_child(server):
    operation = server.operation('Document.GetChild')
    operation.params({'name': 'workspaces'})
    operation.input('/default-domain')
    res = operation.execute()
    assert res['entity-type'] == 'document'
    assert res['properties']['dc:title'] == 'Workspaces'


def test_document_get_child_unknown(server):
    operation = server.operation('Document.GetChild')
    operation.params({'name': 'Workspaces'})
    operation.input('/default-domain')
    with pytest.raises(HTTPError) as e:
        operation.execute()
    assert e.value.response.status_code == 404


def test_params_setter(server):
    operation = server.operation('Noop')
    operation.params({'param1': 'foo', 'param2': 'bar'})
    params = operation.params()
    assert params['param1'] == 'foo'
    assert params['param2'] == 'bar'
    operation.params({'param3': 'plop'})
    operation.params({'param1': 'bar'})
    params = operation.params()
    assert params['param1'] == 'bar'
    assert params['param2'] == 'bar'
    assert params['param3'] == 'plop'
