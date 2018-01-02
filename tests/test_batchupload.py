# coding: utf-8
from __future__ import unicode_literals

import hashlib
import os
import pytest

from nuxeo.exceptions import HTTPError, InvalidBatch
from nuxeo.models import BufferBlob, FileBlob, Document

new_doc = Document(
    name='Document',
    type='File',
    properties={
        'dc:title': 'foo',
    }
)


@pytest.fixture(scope='function')
def batch(server):
    batch = server.uploads.batch()
    assert batch
    batch.upload(BufferBlob(data='data', name='Test.txt', mimetype='text/plain'))
    assert batch.uid
    return batch


def test_cancel(batch):
    batch.upload(BufferBlob(data='data', name='Test.txt', mimetype='text/plain'))
    assert batch.uid
    batch.cancel()
    assert batch.uid is None
    batch.cancel()
    with pytest.raises(InvalidBatch):
        batch.get(0)


def test_fetch(batch):
    blob = batch.get(0)
    assert not blob.fileIdx
    assert blob.uploadType == 'normal'
    assert blob.name == 'Test.txt'
    assert blob.size == 4

    blob = batch.blobs[0]
    assert not blob.fileIdx
    assert blob.uploadType == 'normal'
    assert blob.uploaded
    assert blob.uploadedSize == 4


def test_operation(server, batch):
    server.client.set(schemas=['dublincore', 'file'])
    doc = server.documents.create(
        new_doc, parent_path=pytest.ws_root_path)
    try:
        assert doc.properties['file:content'] is None
        operation = server.operations.new('Blob.AttachOnDocument')
        operation.params = {'document': pytest.ws_root_path + '/Document'}
        operation.input_obj = batch.get(0)
        operation.execute()
        doc = server.documents.get(path=pytest.ws_root_path + '/Document')
        assert doc.properties['file:content'] is not None
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b'data'
    finally:
        doc.delete()


def test_iter_content(server, batch):
    file_in, file_out = 'test_in', 'test_out'
    with open(file_in, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024*1024) + b'\x00')

    doc = server.documents.create(new_doc, parent_path=pytest.ws_root_path)
    try:
        batch.upload(FileBlob(file_in, mimetype='application/octet-stream'))
        operation = server.operations.new('Blob.AttachOnDocument')
        operation.params = {'document': pytest.ws_root_path + '/Document'}
        operation.input_obj = batch.get(1)
        operation.execute(void_op=True)

        operation = server.operations.new('Blob.Get')
        operation.input_obj = pytest.ws_root_path + '/Document'
        file_out = operation.execute(file_out=file_out)
        with open(file_in, 'rb') as f:
            md5_in = hashlib.md5(f.read()).hexdigest()
        with open(file_out, 'rb') as f:
            md5_out = hashlib.md5(f.read()).hexdigest()
        assert md5_in == md5_out
    finally:
        doc.delete()
        os.remove(file_in)
        os.remove(file_out)


def test_mimetype():
    test = 'test.bmp'
    with open(test, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024*1024) + b'\x00')
    try:
        blob = FileBlob(test)
        assert blob.mimetype in ['image/bmp', 'image/x-ms-bmp']
    finally:
        os.remove(test)


def test_wrong_batch_id(server):
    batch = server.uploads.batch()
    batch.uid = '1234'
    with pytest.raises(HTTPError):
        batch.get(0)
