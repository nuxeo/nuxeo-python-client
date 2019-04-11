# coding: utf-8
from __future__ import unicode_literals

import threading

import os
import pytest

from nuxeo.compat import text
from nuxeo.exceptions import (CorruptedFile, HTTPError,
                              InvalidBatch, UploadError)
from nuxeo.models import BufferBlob, Document, FileBlob
from nuxeo.utils import SwapAttr
from .server import Server

new_doc = Document(
    name='Document',
    type='File',
    properties={
        'dc:title': 'foo',
    }
)


def get_batch(server):
    batch = server.uploads.batch()
    assert batch
    assert repr(batch)
    assert not server.uploads.get(batch.uid)
    blob = BufferBlob(data='data', name='Test.txt', mimetype='text/plain')
    assert repr(blob)
    batch.upload(blob)
    assert batch.uid
    return batch


def test_cancel(server):
    batch = get_batch(server)
    batch.cancel()
    assert batch.uid is None
    batch.cancel()
    with pytest.raises(InvalidBatch) as e:
        batch.get(0)
    assert text(e.value)
    batch.delete(0)


def test_data():
    blob = BufferBlob(data='data', name='Test.txt', mimetype='text/plain')
    with blob:
        assert blob.data

    test = 'test_file'
    with open(test, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')
    try:
        blob = FileBlob(test)
        with blob:
            assert blob.data
    finally:
        os.remove(test)


@pytest.mark.parametrize('hash, is_valid', [
    # Raises CorruptedFile
    ('0' * 32, False),
    # Bypasses checksum validation
    (None, True),
    ('', True),
    ('foo', True),
])
def test_digester(hash, is_valid, server):
    file_out = 'test_out'
    doc = server.documents.create(new_doc, parent_path=pytest.ws_root_path)
    try:
        batch = get_batch(server)
        operation = server.operations.new('Blob.AttachOnDocument')
        operation.params = {'document': pytest.ws_root_path + '/Document'}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)

        operation = server.operations.new('Blob.Get')
        operation.input_obj = pytest.ws_root_path + '/Document'
        if is_valid:
            operation.execute(file_out=file_out, digest=hash)
        else:
            with pytest.raises(CorruptedFile) as e:
                operation.execute(file_out=file_out, digest=hash)
            assert text(e.value)
    finally:
        doc.delete()
        os.remove(file_out)


@pytest.mark.parametrize('chunked', [False, True])
def test_empty_file(chunked, server):
    batch = server.uploads.batch()
    batch.upload(BufferBlob(data='', name='Test.txt'), chunked=chunked)


def test_execute(server):
    server.client.set(schemas=['dublincore', 'file'])
    doc = server.documents.create(new_doc, parent_path=pytest.ws_root_path)
    try:
        batch = get_batch(server)
        assert not doc.properties['file:content']
        batch.execute('Blob.AttachOnDocument', file_idx=0,
                      params={'document': pytest.ws_root_path + '/Document'})
        doc = server.documents.get(path=pytest.ws_root_path + '/Document')
        assert doc.properties['file:content']
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b'data'
    finally:
        doc.delete()


def test_fetch(server):
    batch = get_batch(server)
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
    batch.delete(0)
    assert not batch.blobs[0]


def test_mimetype():
    test = 'test.bmp'
    with open(test, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')
    try:
        blob = FileBlob(test)
        assert blob.mimetype in ['image/bmp', 'image/x-ms-bmp']
    finally:
        os.remove(test)


def test_operation(server):
    batch = get_batch(server)
    server.client.set(schemas=['dublincore', 'file'])
    doc = server.documents.create(
        new_doc, parent_path=pytest.ws_root_path)
    try:
        assert not doc.properties['file:content']
        operation = server.operations.new('Blob.AttachOnDocument')
        operation.params = {'document': pytest.ws_root_path + '/Document'}
        operation.input_obj = batch.get(0)
        operation.execute()
        doc = server.documents.get(path=pytest.ws_root_path + '/Document')
        assert doc.properties['file:content']
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b'data'
    finally:
        doc.delete()


@pytest.mark.parametrize('chunked', [False, True])
def test_upload(chunked, server):
    def callback(*args):
        assert args

    batch = server.uploads.batch()
    file_in, file_out = 'test_in', 'test_out'
    with open(file_in, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')

    doc = server.documents.create(new_doc, parent_path=pytest.ws_root_path)
    try:
        blob = FileBlob(file_in, mimetype='application/octet-stream')
        assert repr(blob)
        assert batch.upload(blob, chunked=chunked, callback=callback)
        operation = server.operations.new('Blob.AttachOnDocument')
        operation.params = {'document': pytest.ws_root_path + '/Document'}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)

        operation = server.operations.new('Document.Fetch')
        operation.params = {'value': pytest.ws_root_path + '/Document'}
        info = operation.execute()
        digest = info['properties']['file:content']['digest']

        operation = server.operations.new('Blob.Get')
        operation.input_obj = pytest.ws_root_path + '/Document'
        file_out = operation.execute(file_out=file_out, digest=digest)
    finally:
        doc.delete()
        for file_ in (file_in, file_out):
            try:
                os.remove(file_)
            except OSError:
                pass


def test_get_uploader(server):
    def callback(*args):
        assert args

    batch = server.uploads.batch()
    file_in = 'test_in'
    with open(file_in, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')

    try:
        blob = FileBlob(file_in, mimetype='application/octet-stream')
        uploader = batch.get_uploader(
            blob, chunked=True, chunk_size=256 * 1024, callback=callback
        )
        assert str(uploader)
        for idx, _ in enumerate(uploader.iter_upload(), 1):
            assert idx == len(uploader.blob.uploadedChunkIds)

        assert batch.get(0)
    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_uploaderror(server):
    batch = server.uploads.batch()
    file_in = 'test_in'
    with open(file_in, 'wb') as f:
        f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')

    try:
        blob = FileBlob(file_in, mimetype='application/octet-stream')
        assert repr(blob)
        uploader = batch.get_uploader(blob, chunked=True, chunk_size=256 * 1024)
        gen = uploader.iter_upload()

        next(gen)
        next(gen)
        backup = uploader._to_upload
        uploader._to_upload = {0}
        with pytest.raises(UploadError) as e:
            next(gen)
        assert e.value
        assert "already exists" in e.value.info.message
        uploader._to_upload = backup

        for _ in uploader.iter_upload():
            pass

    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_upload_retry(server):
    close_server = threading.Event()
    with SwapAttr(server.client, 'host', 'http://localhost:8081/nuxeo/'):
        try:
            serv = Server.upload_response_server(
                wait_to_close_event=close_server,
                port=8081,
                requests_to_handle=20,
                fail_args={'fail_at': 4, 'fail_number': 1}
            )
            file_in = 'test_in'

            with serv:
                batch = server.uploads.batch()
                with open(file_in, 'wb') as f:
                    f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')
                blob = FileBlob(file_in, mimetype='application/octet-stream')
                batch.upload(blob, chunked=True, chunk_size=256 * 1024)
                close_server.set()  # release server block

        finally:
            try:
                os.remove(file_in)
            except OSError:
                pass


def test_upload_resume(server):
    close_server = threading.Event()
    with SwapAttr(server.client, 'host', 'http://localhost:8081/nuxeo/'):
        try:
            serv = Server.upload_response_server(
                wait_to_close_event=close_server,
                port=8081,
                requests_to_handle=20,
                fail_args={'fail_at': 4, 'fail_number': 3}
            )
            file_in = 'test_in'

            with serv:
                batch = server.uploads.batch()
                with open(file_in, 'wb') as f:
                    f.write(b'\x00' + os.urandom(1024 * 1024) + b'\x00')
                blob = FileBlob(file_in, mimetype='application/octet-stream')
                with pytest.raises(UploadError) as e:
                    batch.upload(blob, chunked=True, chunk_size=256 * 1024)
                assert text(e.value)
                batch.upload(blob, chunked=True, chunk_size=256 * 1024)
                close_server.set()  # release server block

        finally:
            try:
                os.remove(file_in)
            except OSError:
                pass


def test_wrong_batch_id(server):
    batch = server.uploads.batch()
    batch.uid = '1234'
    with pytest.raises(HTTPError):
        batch.get(0)
