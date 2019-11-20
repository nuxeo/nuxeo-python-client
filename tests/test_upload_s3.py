# coding: utf-8
"""
We cannot mock the Nuxeo server with S3 enabled.
So we just test the most crucial part of the upload: S3 calls.
"""
from __future__ import unicode_literals

import os
from uuid import uuid4

import boto3
import pytest
from moto import mock_s3
from nuxeo.compat import text
from nuxeo.constants import UP_AMAZON_S3
from nuxeo.exceptions import HTTPError, UploadError
from nuxeo.handlers.s3 import ChunkUploaderS3, UploaderS3
from nuxeo.models import Batch, FileBlob
from nuxeo.utils import SwapAttr


@pytest.fixture(scope="session")
def aws_pwd():
    return "testing"


@pytest.fixture(scope="session")
def aws_credentials(aws_pwd):
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = aws_pwd
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_pwd
    os.environ["AWS_SECURITY_TOKEN"] = aws_pwd
    os.environ["AWS_SESSION_TOKEN"] = aws_pwd


@pytest.fixture(scope="session")
def s3(aws_credentials):
    with mock_s3():
        s3 = boto3.client("s3", region_name="eu-west-1")

        # Create a bucket
        s3.create_bucket(Bucket="nuxeo-app-transient-prod-testing")

        yield s3


@pytest.fixture(scope="function")
def batch(aws_pwd):
    return Batch(
        **{
            "batchId": text(uuid4()),
            "provider": UP_AMAZON_S3,
            "extraInfo": {
                "bucket": "nuxeo-app-transient-prod-testing",
                "baseKey": "directupload/",
                # "expiration": 1576685943000,
                "useS3Accelerate": False,
                "region": "eu-west-1",
                "awsSecretKeyId": aws_pwd,
                "awsSecretAccessKey": aws_pwd,
                "awsSessionToken": aws_pwd,
            },
        }
    )


def test_upload_not_chunked(s3, batch, server):
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(os.urandom(1024 * 1024 * 5))

    blob = FileBlob(file_in)

    def callback(uploader):
        assert isinstance(uploader, UploaderS3)

    try:
        # Simulate a new single upload
        uploader = server.uploads.get_uploader(batch, blob, callback=callback)
        assert uploader.chunk_count == 1
        uploader.upload()
        assert uploader.is_complete()
        assert uploader.batch.etag is not None

        # Complete the upload, this will not work as there is no real
        # batch ID existant. This is only to have a better coverage.
        batch.service = server.uploads
        with pytest.raises(HTTPError):
            batch.complete()
    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_upload_not_chunked_error(s3, batch, server):
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(os.urandom(1024 * 1024 * 5))

    blob = FileBlob(file_in)

    def put_object(*args, **kwargs):
        raise HTTPError(409, "Conflict", "Mock'ed error")

    # Simulate a single upload that failed
    uploader = server.uploads.get_uploader(batch, blob)

    with SwapAttr(uploader.s3_client, "put_object", put_object):
        try:
            with pytest.raises(UploadError):
                uploader.upload()
            assert uploader.batch.etag is None
        finally:
            try:
                os.remove(file_in)
            except OSError:
                pass


def test_upload_chunked(s3, batch, server):
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024 * 5) + b"\x00")

    blob = FileBlob(file_in)

    def callback1(uploader):
        assert isinstance(uploader, UploaderS3)

    def callback2(uploader):
        assert isinstance(uploader, UploaderS3)

    def get_uploader():
        callbacks = [callback1, callback2]
        return ChunkUploaderS3(
            server.uploads, batch, blob, 256 * 1024, s3_client=s3, callback=callbacks
        )

    # For code coverage ...
    batch.provider = UP_AMAZON_S3
    assert isinstance(
        server.uploads.get_uploader(batch, blob, chunked=True, chunk_size=1024 * 1024),
        ChunkUploaderS3,
    )

    try:
        # Simulate a chunked upload
        uploader = get_uploader()
        assert uploader.chunk_count == 2
        assert uploader._data_packs == []
        assert len(uploader.blob.uploadedChunkIds) == 0
        uploader.upload()
        assert uploader.is_complete()
        assert uploader.batch.etag is not None
    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_upload_chunked_resume(s3, batch, server):
    file_in = "test_in"
    MiB = 1024 * 1024
    with open(file_in, "wb") as f:
        f.write(os.urandom(25 * MiB))

    blob = FileBlob(file_in)

    def get_uploader():
        return ChunkUploaderS3(
            server.uploads, batch, blob, 5 * MiB, s3_client=s3, max_parts=2
        )

    try:
        # Simulate a new upload that will fail
        uploader = get_uploader()
        assert uploader.chunk_count == 5
        assert uploader._data_packs == []
        assert len(uploader.blob.uploadedChunkIds) == 0

        # Upload 4 parts (out of 5) and then fail
        uploaded_parts = []
        for part in range(1, 5):
            next(uploader.iter_upload())
            uploaded_parts.append(part)
            assert uploader.blob.uploadedChunkIds == uploaded_parts
            assert len(uploader._data_packs) == len(uploaded_parts)
            for data_pack in uploader._data_packs:
                assert isinstance(data_pack, dict)
                assert data_pack["PartNumber"] in uploaded_parts
                assert "ETag" in data_pack
            assert not uploader.is_complete()
            assert uploader.batch.etag is None

        # Simulate a resume of the same upload, it should succeed
        # (AWS details are stored into the *batch* object, that's why it works)
        uploader = get_uploader()
        assert uploader.chunk_count == 5
        assert len(uploader._data_packs) == 4
        assert uploader.blob.uploadedChunkIds == [1, 2, 3, 4]
        uploader.upload()
        assert uploader.blob.uploadedChunkIds == [1, 2, 3, 4, 5]
        assert uploader.is_complete()
        assert uploader.batch.etag is not None
    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_upload_chunked_error(s3, batch, server):
    file_in = "test_in"
    with open(file_in, "wb") as f:
        f.write(b"\x00" + os.urandom(1024 * 1024 * 5) + b"\x00")

    blob = FileBlob(file_in)

    def upload_part(*args, **kwargs):
        raise HTTPError(409, "Conflict", "Mock'ed error")

    def get_uploader():
        return ChunkUploaderS3(server.uploads, batch, blob, 256 * 1024, s3_client=s3)

    try:
        # Simulate a new upload that failed at after the first uploaded part
        uploader = get_uploader()
        assert uploader.chunk_count == 2
        assert uploader._data_packs == []
        assert len(uploader.blob.uploadedChunkIds) == 0
        with SwapAttr(uploader.s3_client, "upload_part", upload_part):
            with pytest.raises(UploadError):
                next(uploader.iter_upload())
        assert not uploader.is_complete()

        # Retry should work
        uploader.upload()
        assert uploader.is_complete()
        assert uploader.batch.etag is not None
    finally:
        try:
            os.remove(file_in)
        except OSError:
            pass


def test_wrong_multipart_upload_id(s3, batch, server):
    batch.multiPartUploadId = "1234"

    file_in = "test_in"
    MiB = 1024 * 1024
    with open(file_in, "wb") as f:
        f.write(os.urandom(5 * MiB))

    blob = FileBlob(file_in)

    batch.provider = UP_AMAZON_S3
    uploader = server.uploads.get_uploader(
        batch, blob, chunked=True, chunk_size=1024 * 1024
    )
    uploader.s3_client = s3
    assert uploader.batch.multiPartUploadId != "1234"
