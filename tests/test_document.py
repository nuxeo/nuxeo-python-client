# coding: utf-8
from __future__ import unicode_literals

import pytest


def test_document_create(server, repository):
    operation = server.operation('Document.Create')
    operation.params({
        'type': 'File',
        'name': 'foo.txt',
        'properties': {'dc:title': 'foo.txt',
                       'dc:description': 'bar'}
    })
    operation.input('/')
    doc = operation.execute()
    assert doc['entity-type'] == 'document'
    assert doc['type'] == 'File'
    assert doc['title'] == 'foo.txt'
    assert doc['properties']['dc:title'] == 'foo.txt'
    assert doc['properties']['dc:description'] == 'bar'

    repository.delete('/' + doc['title'])
    assert not repository.exists('/' + doc['title'])


def test_document_create_properties_as_str(server, repository):
    operation = server.operation('Document.Create')
    operation.params({
        'type': 'File',
        'name': 'foo.txt',
        'properties': 'dc:title=foo.txt\ndc:description=bar',
    })
    operation.input('/')
    doc = operation.execute()
    assert doc['entity-type'] == 'document'
    assert doc['type'] == 'File'
    assert doc['title'] == 'foo.txt'
    assert doc['properties']['dc:title'] == 'foo.txt'
    assert doc['properties']['dc:description'] == 'bar'
    repository.delete('/' + doc['title'])
    assert not repository.exists('/' + doc['title'])


def test_document_list_update(server):
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
    doc1 = server.repository().create(pytest.ws_root_path, new_doc1)
    doc2 = server.repository().create(pytest.ws_root_path, new_doc2)
    desc = 'sample description'
    operation = server.operation('Document.Update')
    operation.params({'properties': {'dc:description': desc}})
    operation.input([doc1.path, doc2.path])
    res = operation.execute()
    assert res['entity-type'] == 'documents'
    assert len(res['entries']) == 2
    assert res['entries'][0]['path'] == doc1.path
    assert res['entries'][0]['properties']['dc:description'] == desc
    assert res['entries'][1]['path'] == doc2.path
    assert res['entries'][1]['properties']['dc:description'] == desc
    doc1.delete()
    doc2.delete()
