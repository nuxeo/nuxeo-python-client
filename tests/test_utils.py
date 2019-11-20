# coding: utf-8
from __future__ import unicode_literals
import sys

import pytest
from nuxeo.constants import UP_AMAZON_S3
from nuxeo.utils import (
    SwapAttr,
    chunk_partition,
    get_digester,
    guess_mimetype,
    log_chunk_details,
)
from sentry_sdk import configure_scope


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


# We do not need to set-up a server and log the current test
skip_logging = True


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
        # Text
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
        # See /NXP-11660 http://bugs.python.org/issue15207
        ("foo.xml", ("text/xml", "application/xml")),
        ("foo.svg", ("image/svg+xml", "application/octet-stream", "image/svg+xml")),
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
        assert guess_mimetype(name) == mime


def test_guess_mimetype_patch():
    """ Test WIN32_PATCHED_MIME_TYPES. """

    with SwapAttr(sys, "platform", "win32"):
        assert guess_mimetype("foo.ppt")


@pytest.mark.parametrize(
    "chunk_count, chunk_size, uploaded_chunks", [(0, 0, 0), (1, 1024, 3)]
)
def test_log_chunk_details(chunk_count, chunk_size, uploaded_chunks):
    log_chunk_details(chunk_count, chunk_size, uploaded_chunks)
