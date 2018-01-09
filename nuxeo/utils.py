# coding: utf-8
from __future__ import unicode_literals

import logging
import mimetypes
import sys

import hashlib

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, Text, Type
except ImportError:
    pass

WIN32_PATCHED_MIME_TYPES = {
    'image/pjpeg': 'image/jpeg',
    'image/x-png': 'image/png',
    'image/bmp': 'image/x-ms-bmp',
    'audio/x-mpg': 'audio/mpeg',
    'video/x-mpeg2a': 'video/mpeg',
    'application/x-javascript': 'application/javascript',
    'application/x-msexcel': 'application/vnd.ms-excel',
    'application/x-mspowerpoint': 'application/vnd.ms-powerpoint',
    'application/x-mspowerpoint.12':
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}


def get_digester(digest):
    """
    Get digester corresponding to the given hash.

    To choose the digester used by the server, see
    https://doc.nuxeo.com/nxdoc/file-storage-configuration/#configuring-the-default-blobprovider
    :param digest: the hash
    :return: the digester function
    """
    if not digest:
        return None

    digesters = {32: 'md5', 40: 'sha1', 64: 'sha256', 128: 'sha512'}
    try:
        int(digest, 16) >= 0
    except ValueError:
        return None
    algo = digesters.get(len(digest), None)
    digester = getattr(hashlib, algo, None)
    if digester is None:
        logging.debug(
            "Digest can't be traced to a hash algorithm: {}".format(digest))
    return digester


def guess_mimetype(filename):
    # type: (Text) -> Text
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if sys.platform == 'win32':
            # Patch bad Windows MIME types
            # See http://bugs.python.org/issue15207 and NXP-11660
            mime_type = WIN32_PATCHED_MIME_TYPES.get(mime_type, mime_type)
        return mime_type

    return 'application/octet-stream'


def json_helper(obj):
    # type: (Any) -> Dict[Text, Any]
    try:
        return obj.to_json()
    except AttributeError:
        raise TypeError(
            repr(obj) + ' is not JSON serializable (no to_json() found)')


class SwapAttr:
    """
    Context manager to swap an attribute's value:

        >>> # self.person equals 'Alice'
        >>> with SwapAttr(self, 'person', 'Bob'):
        ...     # ...

    """

    def __init__(self, cls, attr, value):
        # type: (Any, Text, Any) -> None
        if not hasattr(cls, attr):
            raise AttributeError()

        self.cls = cls
        self.attr = attr
        self.value = value
        self.old_value = getattr(cls, attr)

    def __enter__(self):
        # type: () -> None
        setattr(self.cls, self.attr, self.value)

    def __exit__(self, *args):
        # type: (Any) -> None
        setattr(self.cls, self.attr, self.old_value)
