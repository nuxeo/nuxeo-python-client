# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.models import Document


def test_document_create(server):
    doc = Document(
        type='File',
        name='日本.txt',
        properties={'dc:title': '日本.txt',
                    'dc:description': 'ру́сский'}
    )
    doc = server.documents.create(doc, parent_path='/')
    assert doc.entity_type == 'document'
    assert doc.type == 'File'
    assert doc.title == '日本.txt'
    assert doc.properties['dc:title'] == '日本.txt'
    assert doc.properties['dc:description'] == 'ру́сский'
    doc.delete()
    assert not server.documents.exists(doc.uid)


def test_document_create_properties_as_str(server):
    operation = server.operations.new('Document.Create')
    operation.params = {
        'type': 'File',
        'name': 'ру́сский.txt',
        'properties': 'dc:title=ру́сский.txt\ndc:description=日本',
    }
    operation.input_obj = '/'
    doc = Document.parse(operation.execute())
    assert doc.entity_type == 'document'
    assert doc.type == 'File'
    assert doc.title == 'ру́сский.txt'
    assert doc.properties['dc:title'] == 'ру́сский.txt'
    assert doc.properties['dc:description'] == '日本'
    server.documents.delete(doc.id)
    assert not server.documents.exists(path='/' + doc.title)


def test_document_list_update(server):
    new_doc1 = Document(
        name='ws-js-tests1',
        type='Workspace',
        properties={
            'dc:title': 'ws-js-tests1',
        })
    new_doc2 = Document(
        name='ws-js-tests2',
        type='Workspace',
        properties={
            'dc:title': 'ws-js-tests2',
        })

    doc1 = server.documents.create(new_doc1, parent_path=pytest.ws_root_path)
    doc2 = server.documents.create(new_doc2, parent_path=pytest.ws_root_path)
    desc = 'sample description'
    res = server.operations.execute(
        'Document.Update',
        params={'properties': {'dc:description': desc}},
        input_obj=[doc1.path, doc2.path])

    assert res['entity-type'] == 'documents'
    assert len(res['entries']) == 2
    assert res['entries'][0]['path'] == doc1.path
    assert res['entries'][0]['properties']['dc:description'] == desc
    assert res['entries'][1]['path'] == doc2.path
    assert res['entries'][1]['properties']['dc:description'] == desc
    doc1.delete()
    doc2.delete()


def test_document_move(server, doc):
    folder = Document(
        name='Test',
        type='Folder',
        properties={
            'dc:title': 'Test'
        })
    f = server.documents.create(folder, parent_path=pytest.ws_root_path)
    try:
        doc.move(pytest.ws_root_path + '/Test', 'new name')
        assert doc.path == pytest.ws_root_path + '/Test/new name'
    finally:
        doc.delete()
        f.delete()


def test_follow_transition(doc):
    assert doc.state == 'project'
    doc.follow_transition('approve')
    assert doc.state == 'approved'
    doc.follow_transition('backToProject')
    assert doc.state == 'project'
    doc.delete()
