# coding: utf-8
"""
We cannot mock the Nuxeo server with S3 enabled.
So we just test the most crucial part of the upload: S3 calls.
"""
import os
from unittest.mock import patch

import boto3
import pytest
import requests.exceptions
from moto import mock_s3
from nuxeo.constants import UP_AMAZON_S3
from nuxeo.exceptions import HTTPError, UploadError
from nuxeo.handlers.s3 import ChunkUploaderS3, UploaderS3
from nuxeo.models import FileBlob

from .constants import SSL_VERIFY


@pytest.fixture(scope="session")
def aws_pwd():
    return "testing"


@pytest.fixture(scope="session")
def aws_credentials(aws_pwd):
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = aws_pwd
    os.environ["AWS_SECRET_ACCESS_KEY"] = aws_pwd
    os.environ["AWS_SESSION_TOKEN"] = aws_pwd


@pytest.fixture(scope="session")
def bucket():
    return "nuxeo-app-transient-prod-testing"


@pytest.fixture
def s3(aws_credentials, bucket):
    with mock_s3():
        client = boto3.client(UP_AMAZON_S3, region_name="eu-west-1")

        # Create a bucket
        client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )

        yield client


@pytest.fixture
def batch(aws_pwd, bucket, server):
    # TODO: when using a real server with S3 configured, just use:
    #   obj = server.uploads.batch(handler=UP_AMAZON_S3)
    obj = server.uploads.batch()
    obj.provider = UP_AMAZON_S3
    obj.extraInfo = {
        "bucket": bucket,
        "baseKey": "directupload/",
        "usePathStyleAccess": False,
        "endpoint": "",
        "expiration": 1576685943000,
        "useS3Accelerate": False,
        "region": "eu-west-1",
        "awsSecretKeyId": aws_pwd,
        "awsSecretAccessKey": aws_pwd,
        "awsSessionToken": aws_pwd,
    }
    assert obj.is_s3()
    return obj


def test_upload_blob_with_bad_characters(tmp_path, batch, bucket, server, s3):
    file_in = tmp_path / "file_in (1).bin"
    file_in.write_bytes(os.urandom(1024 * 1024 * 5))

    blob = FileBlob(str(file_in))

    # Simulate a single upload that failed
    uploader = UploaderS3(server.uploads, batch, blob, 1024 * 1024 * 10, s3_client=s3)

    # Upload he file, it must work
    uploader.upload()
    assert uploader.batch.etag is not None


def test_upload_not_chunked(tmp_path, batch, bucket, server, s3):
    file_in = tmp_path / "file_in"
    file_in.write_bytes(os.urandom(1024 * 1024 * 5))

    blob = FileBlob(str(file_in))

    # Simulate a new single upload
    uploader = UploaderS3(server.uploads, batch, blob, 1024 * 1024 * 10, s3_client=s3)

    assert uploader.chunk_count == 1
    uploader.upload()
    assert uploader.is_complete()
    assert uploader.batch.etag is not None

    # Complete the upload
    batch.service = server.uploads
    # Simple check for additional arguments
    with pytest.raises(requests.exceptions.ConnectionError) as exc:
        batch.complete(timeout=(0.000001, 0.000001))
    error = str(exc.value)
    assert "timed out" in error

    # This will not work as there is no real
    # batch ID existant. This is only to have a better coverage.
    with pytest.raises(HTTPError):
        batch.complete(ssl_verify=SSL_VERIFY)


def test_upload_not_chunked_error(tmp_path, batch, bucket, server, s3):
    file_in = tmp_path / "file_in"
    file_in.write_bytes(os.urandom(1024 * 1024 * 5))

    blob = FileBlob(str(file_in))

    def put_object(*args, **kwargs):
        raise HTTPError(409, "Conflict", "Mock'ed error")

    # Simulate a single upload that failed
    uploader = UploaderS3(server.uploads, batch, blob, 1024 * 1024 * 10, s3_client=s3)

    with patch.object(uploader.s3_client, "put_object", new=put_object):
        with pytest.raises(UploadError):
            uploader.upload()
        assert uploader.batch.etag is None


def test_upload_chunked(tmp_path, s3, batch, server):
    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024 * 5) + b"\x00")

    blob = FileBlob(str(file_in))

    def callback1(uploader):
        assert isinstance(uploader, UploaderS3)

    def callback2(uploader):
        assert isinstance(uploader, UploaderS3)

    def get_uploader():
        callbacks = [callback1, callback2]
        return ChunkUploaderS3(
            server.uploads, batch, blob, 256 * 1024, s3_client=s3, callback=callbacks
        )

    # Simulate a chunked upload
    uploader = get_uploader()
    assert uploader.chunk_count == 2
    assert uploader._data_packs == []
    assert len(uploader.blob.uploadedChunkIds) == 0
    uploader.upload()
    assert uploader.is_complete()
    assert uploader.batch.etag is not None


def test_upload_chunked_resume(tmp_path, s3, batch, server):
    file_in = tmp_path / "file_in"
    MiB = 1024 * 1024
    file_in.write_bytes(os.urandom(25 * MiB))

    blob = FileBlob(str(file_in))

    def get_uploader():
        return ChunkUploaderS3(
            server.uploads, batch, blob, 5 * MiB, s3_client=s3, max_parts=2
        )

    # Simulate a new upload that will fail
    uploader = get_uploader()
    assert uploader.chunk_count == 5
    assert uploader._data_packs == []
    assert len(uploader.blob.uploadedChunkIds) == 0

    iterator = uploader.iter_upload()

    # Upload 4 parts (out of 5) and then fail
    uploaded_parts = []
    for part in range(1, 5):
        next(iterator)
        uploaded_parts.append(part)
        assert uploader.blob.uploadedChunkIds == uploaded_parts
        assert len(uploader._data_packs) == len(uploaded_parts)
        for data_pack in uploader._data_packs:
            assert isinstance(data_pack, dict)
            assert data_pack["PartNumber"] in uploaded_parts
            assert "ETag" in data_pack
        assert not uploader.is_complete()
        assert uploader.batch.etag is None

    # Ask for new tokens, the upload should continue without issue
    # TODO: cannot be tested until using a real server configured with S3
    # old_info = batch.extraInfo.copy()
    # uploader.refresh_token()
    # new_info = batch.extraInfo.copy()
    # for key in ("awsSecretKeyId", "awsSecretAccessKey", "awsSessionToken"):
    #     assert old_info[key] != new_info[key]
    # assert old_info["expiration"] <= new_info["expiration"]

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


def test_upload_chunked_error(tmp_path, s3, batch, server):
    file_in = tmp_path / "file_in"
    file_in.write_bytes(b"\x00" + os.urandom(1024 * 1024 * 5) + b"\x00")

    blob = FileBlob(str(file_in))

    def upload_part(*args, **kwargs):
        raise HTTPError(409, "Conflict", "Mock'ed error")

    def get_uploader():
        return ChunkUploaderS3(server.uploads, batch, blob, 256 * 1024, s3_client=s3)

    # Simulate a new upload that failed at after the first uploaded part
    uploader = get_uploader()
    assert uploader.chunk_count == 2
    assert uploader._data_packs == []
    assert len(uploader.blob.uploadedChunkIds) == 0

    iterator = uploader.iter_upload()

    with patch.object(uploader.s3_client, "upload_part", new=upload_part):
        with pytest.raises(UploadError):
            next(iterator)
    assert not uploader.is_complete()

    # Retry should work
    uploader.upload()
    assert uploader.is_complete()
    assert uploader.batch.etag is not None


def test_wrong_multipart_upload_id(tmp_path, s3, batch, server):
    file_in = tmp_path / "file_in"
    MiB = 1024 * 1024
    file_in.write_bytes(os.urandom(6 * MiB))

    blob = FileBlob(str(file_in))

    batch.multiPartUploadId = "1234"

    with pytest.raises(Exception) as e:
        ChunkUploaderS3(server.uploads, batch, blob, 1024 * 1024 * 5, s3_client=s3)

    error_str = str(e.value)
    assert "NoSuchUpload" in error_str
