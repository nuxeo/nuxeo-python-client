# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.blob import BufferBlob


@pytest.fixture(scope='function')
def batch(server):
    batch = server.batch_upload()
    assert batch is not None
    assert batch.get_batch_id() is None
    batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
    assert batch.get_batch_id() is not None
    return batch


def test_cancel(batch):
    batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
    assert batch.get_batch_id() is not None
    batch.cancel()
    assert batch.get_batch_id() is None


def test_fetch(batch):
    blob = batch.fetch(0)
    assert blob.fileIdx == 0
    assert blob.uploadType == 'normal'
    assert blob.get_name() == 'Test.txt'
    assert blob.get_size() == 4


def test_operation(server, batch):
    new_doc = {
        'name': 'Document',
        'type': 'File',
        'properties': {
            'dc:title': 'foo',
        }
    }
    doc = server.repository(schemas=['dublincore', 'file']).create(
        '/default-domain/workspaces', new_doc)
    try:
        assert doc.properties['file:content'] is None
        operation = server.operation('Blob.AttachOnDocument')
        operation.params({'document': '/default-domain/workspaces/Document'})
        operation.input(batch.fetch(0))
        operation.execute()
        doc = server.repository(schemas=['dublincore', 'file']).fetch(
            '/default-domain/workspaces/Document')
        assert doc.properties['file:content'] is not None
        assert doc.fetch_blob() == 'data'
    finally:
        doc.delete()


def test_upload(batch):
    blob = batch.blobs[0]
    assert blob.fileIdx == 0
    assert blob.uploadType == 'normal'
    assert blob.uploaded
    assert blob.uploadedSize == 4
