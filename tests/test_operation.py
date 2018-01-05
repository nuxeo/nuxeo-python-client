# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.exceptions import HTTPError


def test_document_fetch_by_property(server):
    operation = server.operations.new('Document.FetchByProperty')
    operation.params = {'property': 'dc:title', 'values': 'Workspaces'}
    res = operation.execute()
    assert res['entity-type'] == 'documents'
    assert len(res['entries']) == 1
    assert res['entries'][0]['properties']['dc:title'] == 'Workspaces'


def test_document_fetch_by_property_params_validation(server):
    """ Missing mandatory params. """
    operation = server.operations.new('Document.FetchByProperty')
    operation.params = {'property': 'dc:title'}
    with pytest.raises(ValueError):
        operation.execute(check_params=True)


def test_document_get_child(server):
    operation = server.operations.new('Document.GetChild')
    operation.params = {'name': 'workspaces'}
    operation.input_obj = '/default-domain'
    res = operation.execute()
    assert res['entity-type'] == 'document'
    assert res['properties']['dc:title'] == 'Workspaces'


def test_document_get_child_unknown(server):
    operation = server.operations.new('Document.GetChild')
    operation.params = {'name': 'Workspaces'}
    operation.input_obj = '/default-domain'
    with pytest.raises(HTTPError) as e:
        operation.execute()
    assert e.value.status == 404


def test_params_setter(server):
    operation = server.operations.new('Noop')
    operation.params = {'param1': 'foo', 'param2': 'bar'}
    params = operation.params
    assert params['param1'] == 'foo'
    assert params['param2'] == 'bar'
    operation.params.update({'param3': 'plop'})
    operation.params.update({'param1': 'bar'})
    params = operation.params
    assert params['param1'] == 'bar'
    assert params['param2'] == 'bar'
    assert params['param3'] == 'plop'
