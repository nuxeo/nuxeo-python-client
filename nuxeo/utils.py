# coding: utf-8
from __future__ import unicode_literals

import logging
import mimetypes
import sys

import hashlib

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from _hashlib import HASH  # noqa
        from typing import Any, Dict, Optional, Text, Type, Union  # noqa
except ImportError:
    pass


logger = logging.getLogger(__name__)
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
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}


def get_digest_algorithm(digest):
    # type: (Text) -> Optional[Text]

    # Available algorithms
    digesters = {
        32: 'md5',
        40: 'sha1',
        56: 'sha224',
        64: 'sha256',
        96: 'sha384',
        128: 'sha512',
    }

    # Ensure the digest is hexadecimal
    try:
        int(digest, 16) >= 0
    except (TypeError, ValueError):
        return None

    return digesters.get(len(digest), None)


def get_digest_hash(algorithm):
    # type: (Text) -> Optional[HASH]

    # Retrieve the hashlib function for the given digest, None if not found
    func = getattr(hashlib, algorithm, None)

    return func() if func else None


def get_digester(digest):
    # type: (Text) -> Optional[HASH]
    """
    Get the digester corresponding to the given hash.

    To choose the digester used by the server, see
    https://doc.nuxeo.com/nxdoc/file-storage-configuration/#configuring-the-default-blobprovider

    :param digest: the hash
    :return: the digester function
    """

    algo = get_digest_algorithm(digest)
    func = get_digest_hash(algo) if algo else None

    if not func:
        logger.error('No valid hash algorithm found for digest %r', digest)

    return func


def guess_mimetype(filename):
    # type: (Text) -> Text
    """ Guess the mimetype of a given file. """
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
    return obj.to_json()


class SwapAttr(object):
    """
    Context manager to swap an attribute's value:

        >>> # self.person equals 'Alice'
        >>> with SwapAttr(self, 'person', 'Bob'):
        ...     # ...

    """

    def __init__(self, obj, attr, value):
        # type: (Any, Text, Any) -> None
        self.obj = obj
        self.attr = attr
        self.value = value
        self.old_value = getattr(obj, attr)

    def __enter__(self):
        # type: () -> None
        setattr(self.obj, self.attr, self.value)

    def __exit__(self, *args):
        # type: (Any) -> None
        setattr(self.obj, self.attr, self.old_value)
