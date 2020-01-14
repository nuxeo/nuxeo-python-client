# coding: utf-8
from __future__ import unicode_literals

import threading

import os
import pytest

from nuxeo.compat import text
from nuxeo.exceptions import (
    CorruptedFile,
    HTTPError,
    InvalidBatch,
    InvalidUploadHandler,
    UploadError,
)
from nuxeo.models import BufferBlob, Document, FileBlob
from nuxeo.utils import SwapAttr
from sentry_sdk import configure_scope

from .constants import WORKSPACE_ROOT
from .server import Server

new_doc = Document(name="Document", type="File", properties={"dc:title": "foo"})


def get_batch(server):
    batch = server.uploads.batch()
    assert batch
    assert repr(batch)
    assert batch.uid
    assert batch.upload_idx == 0
    assert not server.uploads.get(batch.uid)

    blob = BufferBlob(data="data", name="Test.txt", mimetype="text/plain")
    assert repr(blob)
    batch.upload(blob)
    assert batch.upload_idx == 1

    blob2 = BufferBlob(data="data2", name="Test2.txt", mimetype="text/plain")
    batch.upload(blob2)
    assert batch.upload_idx == 2

    return batch


def test_batch_handler_default(server):
    server.uploads.batch(handler="default")


def test_batch_handler_inexistant(server):
    with pytest.raises(InvalidUploadHandler) as exc:
        server.uploads.batch(handler="light")
    error = text(exc.value)
    assert "light" in error
    assert "default" in error


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
    blob = BufferBlob(data="data", name="Test.txt", mimetype="text/plain")
    with blob:
        assert blob.data

    test = "test_file"
    with open(test, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024) + b"\x00")
    try:
        blob = FileBlob(test)
        with blob:
            assert blob.data
    finally:
        os.remove(test)


@pytest.mark.parametrize(
    "hash, is_valid",
    [
        # Raises CorruptedFile
        ("0" * 32, False),
        # Bypasses checksum validation
        (None, True),
        ("", True),
        ("foo", True),
    ],
)
def test_digester(hash, is_valid, server):
    file_out = "test_out"
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        batch = get_batch(server)
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": WORKSPACE_ROOT + "/Document"}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)

        operation = server.operations.new("Blob.Get")
        operation.input_obj = WORKSPACE_ROOT + "/Document"
        if is_valid:
            operation.execute(file_out=file_out, digest=hash)
        else:
            with pytest.raises(CorruptedFile) as e, configure_scope() as scope:
                scope._should_capture = False
                operation.execute(file_out=file_out, digest=hash)
            assert text(e.value)
    finally:
        doc.delete()
        os.remove(file_out)


@pytest.mark.parametrize("chunked", [False, True])
def test_empty_file(chunked, server):
    batch = server.uploads.batch()
    batch.upload(BufferBlob(data="", name="Test.txt"), chunked=chunked)


def test_execute(server):
    server.client.set(schemas=["dublincore", "file"])
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        batch = get_batch(server)
        assert not doc.properties["file:content"]
        batch.execute(
            "Blob.AttachOnDocument",
            file_idx=0,
            params={"document": WORKSPACE_ROOT + "/Document"},
        )
        doc = server.documents.get(path=WORKSPACE_ROOT + "/Document")
        assert doc.properties["file:content"]
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b"data"
    finally:
        doc.delete()


def test_fetch(server):
    batch = get_batch(server)

    blob = batch.get(0)
    assert not blob.fileIdx
    assert blob.uploadType == "normal"
    assert blob.name == "Test.txt"
    assert blob.size == 4  # "data"

    blob = batch.blobs[0]
    assert blob.fileIdx == 0
    assert blob.uploadType == "normal"
    assert blob.uploaded
    assert blob.uploadedSize == 4  # "data"

    batch.delete(0)
    assert not batch.blobs[0]

    blob = batch.get(1)
    assert blob.fileIdx == 1
    assert blob.uploadType == "normal"
    assert blob.name == "Test2.txt"
    assert blob.size == 5  # "data2"

    blob = batch.blobs[1]
    assert blob.fileIdx == 1
    assert blob.uploadType == "normal"
    assert blob.uploaded
    assert blob.uploadedSize == 5  # "data2"

    batch.delete(1)
    assert not batch.blobs[1]


def test_handlers(server):
    server.uploads._API__handlers = None
    handlers = server.uploads.handlers()
    assert isinstance(handlers, list)
    assert "default" in handlers

    if "s3" in handlers:
        assert server.uploads.has_s3()
    else:
        assert not server.uploads.has_s3()

    # Test the second call does not recall the endpoint, it is cached
    assert server.uploads.handlers() is handlers

    # Test forcing the recall to the endpoint
    forced_handlers = server.uploads.handlers(force=True)
    assert forced_handlers is not handlers


def test_handlers_server_error(server):
    def bad_request(*args, **kwargs):
        raise HTTPError(500, "Server Error", "Mock'ed error")

    with SwapAttr(server.client, "request", bad_request):
        assert server.uploads.handlers(force=True) == []


def test_handlers_custom(server):
    server.uploads._API__handlers = ["custom"]
    with pytest.raises(HTTPError):
        server.uploads.batch(handler="custom")


def test_mimetype():
    test = "test.bmp"
    with open(test, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024) + b"\x00")
    try:
        blob = FileBlob(test)
        assert blob.mimetype in ["image/bmp", "image/x-ms-bmp"]
    finally:
        os.remove(test)


def test_operation(server):
    batch = get_batch(server)
    server.client.set(schemas=["dublincore", "file"])
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        assert not doc.properties["file:content"]
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": WORKSPACE_ROOT + "/Document"}
        operation.input_obj = batch.get(0)
        operation.execute()
        doc = server.documents.get(path=WORKSPACE_ROOT + "/Document")
        assert doc.properties["file:content"]
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b"data"
    finally:
        doc.delete()


@pytest.mark.parametrize("chunked", [False, True])
def test_upload(chunked, server):
    def callback(upload):
        assert upload
        assert isinstance(upload.blob.uploadedChunkIds, list)
        assert isinstance(upload.blob.uploadedSize, int)

        if not chunked:
            assert upload.blob.uploadedSize == file_size
            assert upload.blob.uploadType == "normal"
        else:
            # In chunked mode, we should have 1024, 2048, 3072 and 4096 respectively
            sizes = {1: 1024, 2: 1024 * 2, 3: 1024 * 3, 4: 1024 * 4}
            assert upload.blob.uploadedSize == sizes[len(upload.blob.uploadedChunkIds)]
            assert upload.blob.uploadType == "chunked"

    batch = server.uploads.batch()

    chunk_size = 1024
    file_size = 4096 if chunked else 1024
    file_in, file_out = "test_in", "test_out"
    with open(file_in, "wb") as f:
        f.write(b"\x00" * file_size)

    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        blob = FileBlob(file_in, mimetype="application/octet-stream")
        assert repr(blob)
        assert batch.upload(
            blob, chunked=chunked, callback=callback, chunk_size=chunk_size
        )
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": WORKSPACE_ROOT + "/Document"}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)

        operation = server.operations.new("Document.Fetch")
        operation.params = {"value": WORKSPACE_ROOT + "/Document"}
        info = operation.execute()
        digest = info["properties"]["file:content"]["digest"]

        operation = server.operations.new("Blob.Get")
        operation.input_obj = WORKSPACE_ROOT + "/Document"
        file_out = operation.execute(file_out=file_out, digest=digest)
    finally:
        doc.delete()
        for file_ in (file_in, file_out):
            try:
                os.remove(file_)
            except OSError:
                pass


@pytest.mark.parametrize("chunked", [False, True])
def test_upload_several_callbacks(chunked, server):
    check = 0

    def callback1(upload):
        nonlocal check
        check += 1

    def callback2(upload):
        assert upload
        assert isinstance(upload.blob.uploadedChunkIds, list)
        assert isinstance(upload.blob.uploadedSize, int)

        if not chunked:
            assert upload.blob.uploadedSize == file_size
            assert upload.blob.uploadType == "normal"
        else:
            # In chunked mode, we should have 1024, 2048, 3072 and 4096 respectively
            sizes = {1: 1024, 2: 1024 * 2, 3: 1024 * 3, 4: 1024 * 4}
            assert upload.blob.uploadedSize == sizes[len(upload.blob.uploadedChunkIds)]
            assert upload.blob.uploadType == "chunked"

    batch = server.uploads.batch()

    chunk_size = 1024
    file_size = 4096 if chunked else 1024
    file_in, file_out = "test_in", "test_out"
    with open(file_in, "wb") as f:
        f.write(b"\x00" * file_size)

    callbacks = [callback1, callback2, "callback3"]
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        blob = FileBlob(file_in, mimetype="application/octet-stream")
        assert repr(blob)
        assert batch.upload(
            blob, chunked=chunked, callback=callbacks, chunk_size=chunk_size
        )
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": WORKSPACE_ROOT + "/Document"}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)

        operation = server.operations.new("Document.Fetch")
        operation.params = {"value": WORKSPACE_ROOT + "/Document"}
        info = operation.execute()
        digest = info["properties"]["file:content"]["digest"]

        operation = server.operations.new("Blob.Get")
        operation.input_obj = WORKSPACE_ROOT + "/Document"
        file_out = operation.execute(file_out=file_out, digest=digest)
    finally:
        doc.delete()
        for file_ in (file_in, file_out):
            try:
                os.remove(file_)
            except OSError:
                pass

    # Check the callback count (1 for not chucked)
    assert check == 4 if chunked else 1


def test_get_uploader(server):
    def callback(*args):
        assert args

    batch = server.uploads.batch()
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    try:
        blob = FileBlob(file_in, mimetype="application/octet-stream")
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


def test_upload_error(server):
    batch = server.uploads.batch()
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    try:
        blob = FileBlob(file_in, mimetype="application/octet-stream")
        assert repr(blob)
        uploader = batch.get_uploader(blob, chunked=True, chunk_size=256 * 1024)
        gen = uploader.iter_upload()

        next(gen)
        next(gen)
        backup = uploader._to_upload
        uploader._to_upload = [0]
        with pytest.raises(UploadError) as e:
            next(gen)
        assert e.value
        assert "already exists" in e.value.info
        uploader._to_upload = backup

        for _ in uploader.iter_upload():
            pass

    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_upload_retry(retry_server):
    server = retry_server
    close_server = threading.Event()

    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    with SwapAttr(server.client, "host", "http://localhost:8081/nuxeo/"):
        try:
            serv = Server.upload_response_server(
                wait_to_close_event=close_server,
                port=8081,
                requests_to_handle=20,
                fail_args={"fail_at": 4, "fail_number": 1},
            )

            with serv:
                batch = server.uploads.batch()
                blob = FileBlob(file_in, mimetype="application/octet-stream")
                batch.upload(blob, chunked=True, chunk_size=256 * 1024)
                close_server.set()  # release server block

        finally:
            try:
                os.remove(file_in)
            except OSError:
                pass


def test_upload_resume(server):
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    with SwapAttr(server.client, "host", "http://localhost:8081/nuxeo/"):
        try:
            close_server = threading.Event()
            serv = Server.upload_response_server(
                wait_to_close_event=close_server,
                port=8081,
                requests_to_handle=20,
                fail_args={"fail_at": 4, "fail_number": 1},
            )

            with serv:
                batch = server.uploads.batch()
                blob = FileBlob(file_in, mimetype="application/octet-stream")
                with pytest.raises(UploadError) as e:
                    batch.upload(blob, chunked=True, chunk_size=256 * 1024)
                assert text(e.value)

                # Resume the upload
                batch.upload(blob, chunked=True, chunk_size=256 * 1024)

                # No-op
                batch.complete()

                # Release the server block
                close_server.set()

        finally:
            try:
                os.remove(file_in)
            except OSError:
                pass


def test_wrong_batch_id(server):
    batch = server.uploads.batch()
    batch.uid = "1234"
    with pytest.raises(HTTPError):
        batch.get(0)
