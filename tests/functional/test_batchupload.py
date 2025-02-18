# coding: utf-8
import os
import threading
import uuid
from collections import defaultdict
from unittest.mock import patch
from uuid import uuid4

import pytest
import responses
from nuxeo.constants import IDEMPOTENCY_KEY, UP_AMAZON_S3
from nuxeo.exceptions import (
    CorruptedFile,
    HTTPError,
    InvalidBatch,
    InvalidUploadHandler,
    OngoingRequestError,
    UploadError,
)
from nuxeo.models import Batch, BufferBlob, Document, FileBlob
from requests.exceptions import ConnectionError
from sentry_sdk import configure_scope, get_current_scope, get_isolation_scope

from ..constants import WORKSPACE_ROOT, SSL_VERIFY
from ..server import Server


new_doc = Document(name="Document", type="File", properties={"dc:title": "foo"})


def get_batch(server):
    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
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


def test_token_callback(server):
    original_creds = {
        "bucket": "my-bucket",
        "baseKey": "directupload/",
        "endpoint": None,
        "expiration": 1621345126000,
        "usePathStyleAccess": False,
        "region": "eu-west-1",
        "useS3Accelerate": False,
        "awsSecretKeyId": "...",
        "awsSessionToken": "...",
        "awsSecretAccessKey": "...",
    }
    batch = Batch(batchId=str(uuid4()), extraInfo=original_creds)

    check = {batch.uid: None}

    def callback(my_batch, creds):
        check[my_batch.uid] = creds.copy()

    # Using the default upload provider
    # => the callback is not even called
    creds = server.uploads.refresh_token(batch, token_callback=callback)
    assert creds == {}
    assert check[batch.uid] is None

    url = f"{server.client.host}{server.uploads.endpoint}/{batch.uid}/refreshToken"
    batch.provider = UP_AMAZON_S3

    # Using S3 third-party upload provider, with credentials not expired
    # => new credentials are then the same as current ones
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, url, json=original_creds)

        creds = server.uploads.refresh_token(batch, token_callback=callback)
        assert creds == original_creds
        assert check[batch.uid] is None

    # Using S3 third-party upload provider, with credentials expired
    # => new credentials are recieved
    with responses.RequestsMock() as rsps:
        new_creds = {
            "awsSecretKeyId": "updated 1",
            "awsSessionToken": "updated 2",
            "awsSecretAccessKey": "updated 3",
        }
        rsps.add(responses.POST, url, json=new_creds)

        creds = server.uploads.refresh_token(batch, token_callback=callback)
        assert creds == new_creds
        assert check[batch.uid] == new_creds
        assert batch.extraInfo["awsSecretKeyId"] == "updated 1"
        assert batch.extraInfo["awsSessionToken"] == "updated 2"
        assert batch.extraInfo["awsSecretAccessKey"] == "updated 3"


def test_batch_handler_default(server):
    server.uploads.batch(handler="default", ssl_verify=SSL_VERIFY)


def test_batch_handler_inexistant(server):
    with pytest.raises(InvalidUploadHandler) as exc:
        server.uploads.batch(handler="light", ssl_verify=SSL_VERIFY)
    error = str(exc.value)
    assert "light" in error
    assert "default" in error


def test_batch__post_with_kwarg(server):
    server.uploads.batch(headers={"upload-provider": "nuxeo"}, ssl_verify=SSL_VERIFY)


def test_cancel(server):
    batch = get_batch(server)
    batch.cancel()
    assert batch.uid is None
    batch.cancel()
    with pytest.raises(InvalidBatch) as e:
        batch.get(0, ssl_verify=SSL_VERIFY)
    assert str(e.value)
    batch.delete(0)


def test_data(tmp_path):
    blob = BufferBlob(data="data", name="Test.txt", mimetype="text/plain")
    with blob:
        assert blob.data

    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024) + b"\x00")
    blob = FileBlob(str(file_in))
    with blob:
        assert blob.data


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
def test_digester(tmp_path, hash, is_valid, server):
    file_out = tmp_path / "file_out"
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        batch = get_batch(server)
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": f"{WORKSPACE_ROOT}/Document"}
        operation.input_obj = batch.get(0, ssl_verify=SSL_VERIFY)
        operation.execute(void_op=True)

        operation = server.operations.new("Blob.Get")
        operation.input_obj = f"{WORKSPACE_ROOT}/Document"
        if is_valid:
            operation.execute(file_out=file_out, digest=hash)
        else:
            print(f">>>> configure_scope: {configure_scope()}")
            print(f">>>> get_current_scope: {get_current_scope()}")
            print(f">>>> get_isolation_scope: {get_isolation_scope()}")
            with pytest.raises(CorruptedFile) as e, configure_scope() as scope:
                scope._should_capture = False
                operation.execute(file_out=file_out, digest=hash)
            assert str(e.value)
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)


@pytest.mark.parametrize("chunked", [False, True])
def test_empty_file(chunked, server):
    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
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
            params={"document": f"{WORKSPACE_ROOT}/Document"},
        )
        doc = server.documents.get(
            path=f"{WORKSPACE_ROOT}/Document", ssl_verify=SSL_VERIFY
        )
        assert doc.properties["file:content"]
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b"data"
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)


def test_fetch(server):
    batch = get_batch(server)

    blob = batch.get(0, ssl_verify=SSL_VERIFY)
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

    blob = batch.get(1, ssl_verify=SSL_VERIFY)
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

    if UP_AMAZON_S3 in handlers:
        assert server.uploads.has_s3()
    else:
        assert not server.uploads.has_s3()

    # Test the second call does not recall the endpoint, it is cached
    assert server.uploads.handlers() == handlers

    # Test forcing the recall to the endpoint
    forced_handlers = server.uploads.handlers(force=True)
    assert forced_handlers is not handlers


def test_handlers_server_error(server):
    def bad_request(*args, **kwargs):
        raise HTTPError(500, "Server Error", "Mock'ed error")

    with patch.object(server.client, "request", new=bad_request):
        assert server.uploads.handlers(force=True) == []


def test_handlers_custom(server):
    server.uploads._API__handlers = ["custom"]
    with pytest.raises(HTTPError):
        server.uploads.batch(handler="custom", ssl_verify=SSL_VERIFY)


@pytest.mark.parametrize(
    "filename, mimetypes",
    [
        ("file.bmp", ["image/bmp", "image/x-ms-bmp"]),
        ("file.pdf", ["application/pdf"]),
    ],
)
def test_mimetype(filename, mimetypes, tmp_path, server):
    file_in = tmp_path / filename
    file_in.write_bytes(b"0" * 42)
    blob = FileBlob(str(file_in))
    assert blob.mimetype in mimetypes

    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        # Upload the blob
        batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
        uploader = batch.get_uploader(blob, ssl_verify=SSL_VERIFY)
        uploader.upload()

        # Attach the blob to the doc
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": doc.path}

        operation.input_obj = batch.get(0, ssl_verify=SSL_VERIFY)
        operation.execute(void_op=True)

        # Fetch doc metadata
        operation = server.operations.new("Document.Fetch")
        operation.params = {"value": doc.path}
        info = operation.execute()

        # Check the mimetype set by the server is correct
        mimetype = info["properties"]["file:content"]["mime-type"]
        assert mimetype in mimetypes
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)


@pytest.mark.parametrize(
    "bad_mimetype, expected_mimetype",
    [
        (None, "application/pdf"),
        ("", "application/pdf"),
        ("pdf", "application/pdf"),
    ],
)
def test_bad_mimetype(bad_mimetype, expected_mimetype, tmp_path, server):
    file_in = tmp_path / "file.pdf"
    file_in.write_bytes(b"0" * 42)
    blob = FileBlob(str(file_in), mimetype=bad_mimetype)
    assert blob.mimetype == (bad_mimetype or expected_mimetype)

    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        # Upload the blob
        batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
        uploader = batch.get_uploader(blob)
        uploader.upload()

        # Attach the blob to the doc
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": doc.path}
        operation.input_obj = batch.get(0, ssl_verify=SSL_VERIFY)
        operation.execute(void_op=True)

        # Fetch doc metadata
        operation = server.operations.new("Document.Fetch")
        operation.params = {"value": doc.path}
        info = operation.execute()

        # Check the mimetype set by the server is correct
        mimetype = info["properties"]["file:content"]["mime-type"]
        assert mimetype == expected_mimetype
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)


def test_operation(server):
    batch = get_batch(server)
    server.client.set(schemas=["dublincore", "file"])
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        assert not doc.properties["file:content"]
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": f"{WORKSPACE_ROOT}/Document"}
        operation.input_obj = batch.get(0, ssl_verify=SSL_VERIFY)
        operation.execute()
        doc = server.documents.get(
            path=f"{WORKSPACE_ROOT}/Document", ssl_verify=SSL_VERIFY
        )
        assert doc.properties["file:content"]
        blob = doc.fetch_blob()
        assert isinstance(blob, bytes)
        assert blob == b"data"
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)


@pytest.mark.parametrize("chunked", [False, True])
def test_upload_chunk_timeout(tmp_path, chunked, server):

    chunk_size = 1024
    file_size = 4096 if chunked else chunk_size
    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" * file_size)

    blob = FileBlob(str(file_in), mimetype="application/octet-stream")

    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
    uploader = batch.get_uploader(blob, chunked=chunked, chunk_size=chunk_size)

    assert uploader.timeout(-1) == 60.0
    assert uploader.timeout(0.000001) == 60.0
    assert uploader.timeout(0) == 60.0
    assert uploader.timeout(1) == 60.0
    assert uploader.timeout(1024) == 60.0
    assert uploader.timeout(1024 * 1024) == 60.0 * 1  # 1 MiB
    assert uploader.timeout(1024 * 1024 * 5) == 60.0 * 5  # 5 MiB
    assert uploader.timeout(1024 * 1024 * 10) == 60.0 * 10  # 10 MiB
    assert uploader.timeout(1024 * 1024 * 20) == 60.0 * 20  # 20 MiB
    uploader._timeout = 0.0000000000001
    assert uploader.timeout(chunk_size) == 0.0000000000001
    with pytest.raises(ConnectionError) as exc:
        uploader.upload()
    error = str(exc.value)
    assert "timed out" in error


@pytest.mark.parametrize("chunked", [False, True])
def test_upload(tmp_path, chunked, server):
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

    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)

    chunk_size = 1024
    file_size = 4096 if chunked else 1024
    file_in, file_out = tmp_path / "file_in", tmp_path / "file_out"
    file_in.write_bytes(b"\x00" * file_size)

    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        blob = FileBlob(str(file_in), mimetype="application/octet-stream")
        assert repr(blob)
        assert batch.upload(
            blob, chunked=chunked, callback=callback, chunk_size=chunk_size
        )
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": f"{WORKSPACE_ROOT}/Document"}
        operation.input_obj = batch.get(0, ssl_verify=SSL_VERIFY)
        operation.execute(void_op=True)

        operation = server.operations.new("Document.Fetch")
        operation.params = {"value": f"{WORKSPACE_ROOT}/Document"}
        info = operation.execute()
        digest = info["properties"]["file:content"]["digest"]

        operation = server.operations.new("Blob.Get")
        operation.input_obj = f"{WORKSPACE_ROOT}/Document"
        file_out = operation.execute(file_out=file_out, digest=digest)
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)


@pytest.mark.parametrize("chunked", [False, True])
def test_upload_several_callbacks(tmp_path, chunked, server):
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

    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)

    chunk_size = 1024
    file_size = 4096 if chunked else 1024
    file_in, file_out = tmp_path / "file_in", tmp_path / "file_out"
    file_in.write_bytes(b"\x00" * file_size)

    callbacks = [callback1, callback2, "callback3"]
    doc = server.documents.create(new_doc, parent_path=WORKSPACE_ROOT)
    try:
        blob = FileBlob(str(file_in), mimetype="application/octet-stream")
        assert repr(blob)
        assert batch.upload(
            blob, chunked=chunked, callback=callbacks, chunk_size=chunk_size
        )
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": f"{WORKSPACE_ROOT}/Document"}
        operation.input_obj = batch.get(0, ssl_verify=SSL_VERIFY)
        operation.execute(void_op=True)

        operation = server.operations.new("Document.Fetch")
        operation.params = {"value": f"{WORKSPACE_ROOT}/Document"}
        info = operation.execute()
        digest = info["properties"]["file:content"]["digest"]

        operation = server.operations.new("Blob.Get")
        operation.input_obj = f"{WORKSPACE_ROOT}/Document"
        file_out = operation.execute(file_out=file_out, digest=digest)
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)

    # Check the callback count (1 for not chucked)
    assert check == 4 if chunked else 1


def test_get_uploader(tmp_path, server):
    def callback(*args):
        assert args

    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    blob = FileBlob(str(file_in), mimetype="application/octet-stream")
    uploader = batch.get_uploader(
        blob, chunked=True, chunk_size=256 * 1024, callback=callback
    )
    assert str(uploader)
    for idx, _ in enumerate(uploader.iter_upload(), 1):
        assert idx == len(uploader.blob.uploadedChunkIds)

    assert batch.get(0, ssl_verify=SSL_VERIFY)


def test_upload_error(tmp_path, server):
    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    blob = FileBlob(str(file_in), mimetype="application/octet-stream")
    assert repr(blob)
    uploader = batch.get_uploader(blob, chunked=True, chunk_size=256 * 1024)
    gen = uploader.iter_upload()

    # Upload chunks 0 and 1
    next(gen)
    next(gen)

    # Retry the chunk 0, it should end on a error
    backup = uploader._to_upload
    uploader._to_upload = [0]
    with pytest.raises(UploadError) as e:
        next(gen)

    assert e.value
    assert "already exists" or "Server Error" in e.value.info

    # Finish the upload, it must succeed
    uploader._to_upload = backup
    list(uploader.iter_upload())


def test_upload_retry(tmp_path, retry_server):
    server = retry_server
    close_server = threading.Event()

    file_in = tmp_path / "χρυσαφὶ"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    with patch.object(server.client, "host", new="http://localhost:8081/nuxeo/"):
        serv = Server.upload_response_server(
            wait_to_close_event=close_server,
            port=8081,
            requests_to_handle=20,
            fail_args={"fail_at": 4, "fail_number": 1},
        )

        with serv:
            batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
            blob = FileBlob(str(file_in), mimetype="application/octet-stream")
            batch.upload(blob, chunked=True, chunk_size=256 * 1024)
            close_server.set()  # release server block


def test_upload_resume(tmp_path, server):
    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024) + b"\x00")

    with patch.object(server.client, "host", new="http://localhost:8081/nuxeo/"):
        close_server = threading.Event()
        serv = Server.upload_response_server(
            wait_to_close_event=close_server,
            port=8081,
            requests_to_handle=20,
            fail_args={"fail_at": 4, "fail_number": 1},
        )

        with serv:
            batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
            blob = FileBlob(str(file_in), mimetype="application/octet-stream")

            with pytest.raises(UploadError) as e:
                batch.upload(
                    blob, chunked=True, chunk_size=256 * 1024, ssl_verify=SSL_VERIFY
                )
            assert str(e.value)

            # Resume the upload
            batch.upload(
                blob, chunked=True, chunk_size=256 * 1024, ssl_verify=SSL_VERIFY
            )

            # No-op
            batch.complete()

            # Release the server block
            close_server.set()


def test_wrong_batch_id(server):
    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
    batch.uid = "1234"
    with pytest.raises(HTTPError):
        batch.get(0, ssl_verify=SSL_VERIFY)


def test_idempotent_requests(tmp_path, server):
    """
    - upload a file in chunked mode
    - call 5 times (concurrently) the FileManager.Import operation with that file
    - check there are both conflict errors and only one created document
    """
    file_in = tmp_path / "file_in"
    file_in.write_bytes(os.urandom(1024 * 1024 * 10))

    batch = server.uploads.batch(ssl_verify=SSL_VERIFY)
    blob = FileBlob(str(file_in))
    batch.upload(blob, chunked=True, chunk_size=1024 * 1024)

    idempotency_key = str(uuid.uuid4())
    res = defaultdict(int)

    def func():
        try:
            op = server.operations.execute(
                command="FileManager.Import",
                context={"currentDocument": doc.path},
                input_obj=blob,
                headers={
                    IDEMPOTENCY_KEY: idempotency_key,
                    "X-Batch-No-Drop": "true",
                },
            )
            res[op["uid"]] += 1
        except OngoingRequestError as exc:
            res[str(exc)] += 1

    # Create a folder
    name = str(uuid.uuid4())
    folder = Document(name=name, type="Folder", properties={"dc:title": name})
    doc = server.documents.create(
        folder, parent_path=WORKSPACE_ROOT, ssl_verify=SSL_VERIFY
    )

    try:
        # Concurrent calls to the same endpoint
        threads = [threading.Thread(target=func) for _ in range(5)]
        threads[0].start()
        threads[0].join(0.001)

        for thread in threads[1:]:
            thread.start()
        for thread in threads:
            thread.join()

        # Checks
        # 1 docid + 1 error (both can be present multiple times)
        assert len(res.keys()) == 2
        error = (
            "OngoingRequestError: a request with the idempotency key"
            f" {idempotency_key!r} is already being processed."
        )
        assert error in res

        # Ensure there is only 1 doc on the server
        children = server.documents.get_children(path=doc.path)
        assert len(children) == 1
        assert children[0].title == file_in.name

        # Check calling the same request with the same idempotency key returns always the same result
        current_identical_doc = res[children[0].uid]
        current_identical_errors = res[error]
        for _ in range(10):
            func()
        assert res[error] == current_identical_errors
        assert res[children[0].uid] == current_identical_doc + 10
    finally:
        doc.delete(ssl_verify=SSL_VERIFY)
