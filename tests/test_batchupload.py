# coding: utf-8
from __future__ import unicode_literals

import hashlib
import os

import pytest
import sys
from requests import HTTPError

from nuxeo.batchupload import BatchUpload
from nuxeo.blob import BufferBlob, FileBlob
from nuxeo.exceptions import InvalidBatchException

new_doc = {
    'name': 'Document',
    'type': 'File',
    'properties': {
        'dc:title': 'foo',
    }
}


@pytest.fixture(scope='function')
def batch(server):
    batch = server.batch_upload()
    assert batch
    assert batch.get_batch_id() is None
    batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
    assert batch.get_batch_id()
    return batch


def test_cancel(batch):
    batch.upload(BufferBlob('data', 'Test.txt', 'text/plain'))
    assert batch.get_batch_id()
    batch.cancel()
    assert batch.get_batch_id() is None
    batch.cancel()
    with pytest.raises(InvalidBatchException):
        batch.fetch(0)


def test_fetch(batch):
    blob = batch.fetch(0)
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
    doc = server.repository(schemas=['dublincore', 'file']).create(
        pytest.ws_root_path, new_doc)
    try:
        assert doc.properties['file:content'] is None
        operation = server.operation('Blob.AttachOnDocument')
        operation.params({'document': pytest.ws_root_path + '/Document'})
        operation.input(batch.fetch(0))
        operation.execute()
        doc = server.repository(schemas=['dublincore', 'file']).fetch(
            pytest.ws_root_path + '/Document')
        assert doc.properties['file:content'] is not None
        assert doc.fetch_blob() == 'data'
    finally:
        doc.delete()


def test_iter_content(server, batch):
    file_in, file_out = 'test_in', 'test_out'
    with open(file_in, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024*1024) + b'\x00')

    doc = server.repository().create(pytest.ws_root_path, new_doc)
    try:
        batch.upload(FileBlob(file_in, mimetype='application/octet-stream'))
        operation = server.operation('Blob.AttachOnDocument')
        operation.params({'document': pytest.ws_root_path + '/Document'})
        operation.input(batch.fetch(1))
        operation.execute(void_op=True)

        operation = server.operation('Blob.Get')
        operation.input(pytest.ws_root_path + '/Document')
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


def test_wrong_batch_id(server):
    batch = BatchUpload(server)
    batch.batchid = '1234'
    with pytest.raises(HTTPError):
        batch.fetch(0)
