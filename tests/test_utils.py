# coding: utf-8
import sys
from unittest.mock import patch

import pytest
from nuxeo.constants import UP_AMAZON_S3
from nuxeo.utils import (
    chunk_partition,
    get_digester,
    guess_mimetype,
    log_chunk_details,
    version_compare,
    version_compare_client,
    version_le,
    version_lt,
)
from sentry_sdk import configure_scope

# We do not need to set-up a server and log the current test
skip_logging = True

# File size units
MIB = 1024 * 1024
GIB = MIB * 1024
TIB = GIB * 1024


@pytest.mark.parametrize(
    "file_size, desired_chunk_size, handler, chunk_count, chunk_size",
    [
        # Default handler
        (20 * MIB, 20 * MIB, "default", 1, 20 * MIB),
        (1024, 1, "", 1024, 1),
        (1024, 0, "", 1024, 1),
        (1024, -1, "", 1024, 1),
        (20 * MIB, 20 * MIB, "", 1, 20 * MIB),
        (40 * MIB, 20 * MIB, "", 2, 20 * MIB),
        (6 * GIB, 23 * MIB, "", 268, 23 * MIB),
        (TIB, 20 * MIB, "", 52429, 20 * MIB),
        (TIB, MIB, "", 1048576, MIB),
        # Test unknown upload handler
        (42 * MIB, 42 * MIB, "light", 1, 42 * MIB),
        # Amazon S3
        (20 * MIB, 20 * MIB, UP_AMAZON_S3, 1, 20 * MIB),
        (20 * MIB, 2 * MIB, UP_AMAZON_S3, 4, 5 * MIB),
        (6 * GIB, 23 * MIB, UP_AMAZON_S3, 268, 23 * MIB),
        (6 * GIB, 2 * MIB, UP_AMAZON_S3, 1229, 5 * MIB),
        # Test min file size (5 MiB) and it will at upload
        (4 * MIB, 5 * MIB, UP_AMAZON_S3, 1, 5 * MIB),
        # [s3] Test max file size (160 TiB)
        (160 * TIB, 20 * MIB, UP_AMAZON_S3, 10000, 160 * TIB // 9999),
        # [s3] Test max chunk count (10,000)
        (10000 * 20 * MIB, 5 * MIB, UP_AMAZON_S3, 10000, 10000 * 20 * MIB // 9999),
    ],
)
def test_chunk_partition(
    file_size, desired_chunk_size, handler, chunk_count, chunk_size
):
    assert chunk_partition(file_size, desired_chunk_size, handler) == (
        chunk_count,
        chunk_size,
    )


@pytest.mark.parametrize(
    "hash, digester",
    [
        # Known algos
        ("0" * 32, "md5"),
        ("0" * 40, "sha1"),
        ("0" * 56, "sha224"),
        ("0" * 64, "sha256"),
        ("0" * 96, "sha384"),
        ("0" * 128, "sha512"),
        # Other
        (None, None),
        ("", None),
        ("foo", None),
        ("dead", None),
    ],
)
def test_get_digester(hash, digester):
    if digester:
        assert get_digester(hash).name == digester
    else:
        with configure_scope() as scope:
            scope._should_capture = False
            assert not get_digester(hash)


@pytest.mark.parametrize(
    "name, mime",
    [
        # str
        ("foo.txt", "text/plain"),
        ("foo.html", "text/html"),
        ("foo.css", "text/css"),
        ("foo.csv", "text/csv"),
        ("foo.js", "application/javascript"),
        # Image
        ("foo.jpg", "image/jpeg"),
        ("foo.jpeg", "image/jpeg"),
        ("foo.png", "image/png"),
        ("foo.gif", "image/gif"),
        ("foo.bmp", ("image/x-ms-bmp", "image/bmp")),
        ("foo.tiff", "image/tiff"),
        ("foo.ico", ("image/x-icon", "image/vnd.microsoft.icon")),
        # Audio
        ("foo.mp3", "audio/mpeg"),
        ("foo.vma", ("audio/x-ms-wma", "application/octet-stream")),
        ("foo.wav", ("audio/x-wav", "audio/wav")),
        # Video
        ("foo.mpeg", "video/mpeg"),
        ("foo.mp4", "video/mp4"),
        ("foo.mov", "video/quicktime"),
        ("foo.wmv", ("video/x-ms-wmv", "application/octet-stream")),
        ("foo.avi", ("video/x-msvideo", "video/avi")),
        # Office
        ("foo.doc", "application/msword"),
        ("foo.xls", "application/vnd.ms-excel"),
        ("foo.ppt", "application/vnd.ms-powerpoint"),
        # PDF
        ("foo.pdf", "application/pdf"),
        # Unknown
        ("foo.unknown", "application/octet-stream"),
        ("foo.rvt", "application/octet-stream"),
        # Cases badly handled by Windows
        # See NXP-11660 http://bugs.python.org/issue15207
        ("foo.xml", ("text/xml", "application/xml")),
        ("foo.svg", ("image/svg+xml", "application/octet-stream")),
        ("foo.flv", ("application/octet-stream", "video/x-flv")),
        (
            "foo.docx",
            (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/octet-stream",
            ),
        ),
        (
            "foo.xlsx",
            (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/octet-stream",
            ),
        ),
        (
            "foo.pptx",
            (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/x-mspowerpoint.12",
                "application/octet-stream",
            ),
        ),
        (
            "foo.odt",
            ("application/vnd.oasis.opendocument.text", "application/octet-stream"),
        ),
        (
            "foo.ods",
            (
                "application/vnd.oasis.opendocument.spreadsheet",
                "application/octet-stream",
            ),
        ),
        (
            "foo.odp",
            (
                "application/vnd.oasis.opendocument.presentation",
                "application/octet-stream",
            ),
        ),
    ],
)
def test_guess_mimetype(name, mime):
    if isinstance(mime, tuple):
        assert guess_mimetype(name) in mime
    else:
        print(f"name: {name}, type: {guess_mimetype(name)}")
        assert guess_mimetype(name) == mime


def test_guess_mimetype_patch():
    """Test WIN32_PATCHED_MIME_TYPES."""

    with patch.object(sys, "platform", new="win32"):
        assert guess_mimetype("foo.ppt")


@pytest.mark.parametrize(
    "chunk_count, chunk_size, uploaded_chunks, blob_size",
    [(0, 0, 0, 0), (1, 1024, 3, 1024)],
)
def test_log_chunk_details(chunk_count, chunk_size, uploaded_chunks, blob_size):
    log_chunk_details(chunk_count, chunk_size, uploaded_chunks, blob_size)


@pytest.mark.parametrize(
    "x, y",
    [
        ("7.10", "10.1-SNAPSHOT"),
        ("10.1-SNAPSHOT", "10.1"),
        ("10.1", "10.2-SNAPSHOT"),
        ("10.1", "10.1-HF1"),
        ("10.1-SNAPSHOT", "10.1-SNAPSHOT"),
    ],
)
def test_version_le(x, y):
    assert version_le(x, y)


@pytest.mark.parametrize(
    "x, y",
    [
        ("7.10", "10.1-SNAPSHOT"),
        ("10.1-SNAPSHOT", "10.1"),
        ("10.1", "10.2-SNAPSHOT"),
        ("10.1", "10.1-HF1"),
        ("10.1-SNAPSHOT", "10.1-HF1"),
    ],
)
def test_version_lt(x, y):
    assert version_lt(x, y)


@pytest.mark.parametrize(
    "x, y, result",
    [
        # Releases
        ("5.9.2", "5.9.3", -1),
        ("5.9.3", "5.9.3", 0),
        ("5.9.3", "5.9.2", 1),
        ("5.9.3", "5.8", 1),
        ("5.8", "5.6.0", 1),
        ("5.9.1", "5.9.0.1", 1),
        ("6.0", "5.9.3", 1),
        ("5.10", "5.1.2", 1),
        # Snapshots
        ("5.9.3-SNAPSHOT", "5.9.4-SNAPSHOT", -1),
        ("5.8-SNAPSHOT", "5.9.4-SNAPSHOT", -1),
        ("5.9.4-SNAPSHOT", "5.9.4-SNAPSHOT", 0),
        ("5.9.4-SNAPSHOT", "5.9.3-SNAPSHOT", 1),
        ("5.9.4-SNAPSHOT", "5.8-SNAPSHOT", 1),
        # Releases and snapshots
        ("5.9.4-SNAPSHOT", "5.9.4", -1),
        ("5.9.4-SNAPSHOT", "5.9.5", -1),
        ("5.9.3", "5.9.4-SNAPSHOT", -1),
        ("5.9.4-SNAPSHOT", "5.9.3", 1),
        ("5.9.4", "5.9.4-SNAPSHOT", 1),
        ("5.9.5", "5.9.4-SNAPSHOT", 1),
        # Hotfixes
        ("5.6.0-H35", "5.8.0-HF14", -1),
        ("5.8.0-HF14", "5.8.0-HF15", -1),
        ("5.8.0-HF14", "5.8.0-HF14", 0),
        ("5.8.0-HF14", "5.8.0-HF13", 1),
        ("5.8.0-HF14", "5.6.0-HF35", 1),
        # Releases and hotfixes
        ("5.8.0-HF14", "5.9.1", -1),
        ("5.6", "5.8.0-HF14", -1),
        ("5.8", "5.8.0-HF14", -1),
        ("5.8.0-HF14", "5.6", 1),
        ("5.8.0-HF14", "5.8", 1),
        ("5.9.1", "5.8.0-HF14", 1),
        # Snaphsots and hotfixes
        ("5.8.0-HF14", "5.9.1-SNAPSHOT", -1),
        ("5.7.1-SNAPSHOT", "5.8.0-HF14", -1),
        ("5.8.0-SNAPSHOT", "5.8.0-HF14", -1),
        ("5.8-SNAPSHOT", "5.8.0-HF14", -1),
        ("5.8.0-HF14", "5.7.1-SNAPSHOT", 1),
        ("5.8.0-HF14", "5.8.0-SNAPSHOT", 1),
        ("5.8.0-HF14", "5.8-SNAPSHOT", 1),
        ("5.9.1-SNAPSHOT", "5.8.0-HF14", 1),
        # Snapshot hotfixes
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-HF15-SNAPSHOT", -1),
        ("5.6.0-H35-SNAPSHOT", "5.8.0-HF14-SNAPSHOT", -1),
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-HF14-SNAPSHOT", 0),
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-HF13-SNAPSHOT", 1),
        ("5.8.0-HF14-SNAPSHOT", "5.6.0-HF35-SNAPSHOT", 1),
        # Releases and snapshot hotfixes
        ("5.8.0-HF14-SNAPSHOT", "5.9.1", -1),
        ("5.6", "5.8.0-HF14-SNAPSHOT", -1),
        ("5.8", "5.8.0-HF14-SNAPSHOT", -1),
        ("5.8.0-HF14-SNAPSHOT", "5.6", 1),
        ("5.8.0-HF14-SNAPSHOT", "5.8", 1),
        ("5.9.1", "5.8.0-HF14-SNAPSHOT", 1),
        # Snaphsots and snapshot hotfixes
        ("5.8.0-HF14-SNAPSHOT", "5.9.1-SNAPSHOT", -1),
        ("5.7.1-SNAPSHOT", "5.8.0-HF14-SNAPSHOT", -1),
        ("5.8-SNAPSHOT", "5.8.0-HF14-SNAPSHOT", -1),
        ("5.8.0-SNAPSHOT", "5.8.0-HF14-SNAPSHOT", -1),
        ("5.8.0-HF14-SNAPSHOT", "5.7.1-SNAPSHOT", 1),
        ("5.8.0-HF14-SNAPSHOT", "5.8-SNAPSHOT", 1),
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-SNAPSHOT", 1),
        ("5.9.1-SNAPSHOT", "5.8.0-HF14-SNAPSHOT", 1),
        # Hotfixes and snapshot hotfixes
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-HF14", -1),
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-HF15", -1),
        ("5.8.0-HF14-SNAPSHOT", "5.10.0-HF01", -1),
        ("5.8.0-HF14-SNAPSHOT", "5.6.0-HF35", 1),
        ("5.8.0-HF14-SNAPSHOT", "5.8.0-HF13", 1),
    ],
)
def test_version_compare(x, y, result):
    assert version_compare(x, y) == result


@pytest.mark.parametrize(
    "x, y, result",
    [
        ("0.1", "1.0", -1),
        ("2.0.0626", "2.0.806", -1),
        ("2.0.0805", "2.0.806", -1),
        ("2.0.805", "2.0.1206", -1),
        ("1.0", "1.0", 0),
        ("1.3.0424", "1.3.0424", 0),
        ("1.3.0524", "1.3.0424", 1),
        ("1.4", "1.3.0524", 1),
        ("1.4.0622", "1.3.0524", 1),
        ("1.10", "1.1.2", 1),
        ("2.1.0528", "1.10", 1),
        ("2.0.0905", "2.0.806", 1),
        # Semantic versioning
        ("2.0.805", "2.4.0", -1),
        ("2.1.1130", "2.4.0b1", -1),
        ("2.4.0b1", "2.4.0b2", -1),
        ("2.4.2b1", "2.4.2", -1),
        ("2.4.0b1", "2.4.0b1", 0),
        ("2.4.0b10", "2.4.0b1", 1),
        # Compare to None
        (None, "8.10-HF37", -1),
        (None, "2.0.805", -1),
        (None, None, 0),
        ("8.10-HF37", None, 1),
        ("2.0.805", None, 1),
        # Date based versions are treated as normal versions
        ("10.3-I20180803_0125", "10.1", 1),
        ("10.2-I20180703_0125", "10.3-I20180803_0125", -1),
        ("10.3-I20180803_0125", "10.3-I20180803_0125", 0),
        # Alpha
        ("4.0.0", "4.0.0.32", -1),
        ("4.0.0.1", "4.0.0.32", -1),
        ("4.0.0.32", "4.0.0.32", 0),
        ("4.0.0.42", "4.0.0.32", 1),
    ],
)
def test_version_compare_client(x, y, result):
    assert version_compare_client(x, y) == result
