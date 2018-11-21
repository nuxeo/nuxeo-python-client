# coding: utf-8
from __future__ import unicode_literals
import sys

import pytest

from nuxeo.utils import SwapAttr, get_digester, guess_mimetype


@pytest.mark.parametrize('hash, digester', [
    # Known algos
    ('0' * 32, 'md5'),
    ('0' * 40, 'sha1'),
    ('0' * 56, 'sha224'),
    ('0' * 64, 'sha256'),
    ('0' * 96, 'sha384'),
    ('0' * 128, 'sha512'),
    # Other
    (None, None),
    ('', None),
    ('foo', None),
    ('dead', None),
])
def test_get_digester(hash, digester):
    if not digester:
        assert not get_digester(hash)
    else:
        assert get_digester(hash).name == digester


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

    with SwapAttr(sys, 'platform', 'win32'):
        assert guess_mimetype('foo.ppt')
