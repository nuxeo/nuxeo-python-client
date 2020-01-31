# coding: utf-8
from __future__ import unicode_literals

import hashlib
import logging
import mimetypes
import sys

from nuxeo.constants import UP_AMAZON_S3

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from _hashlib import HASH  # noqa
        from typing import Any, Dict, List, Optional, Text, Tuple, Type, Union  # noqa
except ImportError:
    pass


logger = logging.getLogger(__name__)
WIN32_PATCHED_MIME_TYPES = {
    "image/pjpeg": "image/jpeg",
    "image/x-png": "image/png",
    "image/bmp": "image/x-ms-bmp",
    "audio/x-mpg": "audio/mpeg",
    "video/x-mpeg2a": "video/mpeg",
    "application/x-javascript": "application/javascript",
    "application/x-msexcel": "application/vnd.ms-excel",
    "application/x-mspowerpoint": "application/vnd.ms-powerpoint",
    "application/x-mspowerpoint.12": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def chunk_partition(file_size, desired_chunk_size, handler=""):
    # type: (int, int, Optional[Text]) -> Tuple[int, int]
    """Determine the chunk count and chunk size from
    given *file_size* and *desired_chunk_size*.

    There may be boundaries depending of the given upload *handler*.

    :param file_size: the file size to upload (aka the blob)
    :param desired_chunk_size: the desired chunk size
    :param handler: the upload handler to use
    :return: a tuple of the chunk count and chunk size
    """

    chunk_size_min = 1
    chunk_count_max = None

    # Amazon S3 has some limitations
    if handler == UP_AMAZON_S3:
        chunk_size_min = 1024 * 1024 * 5  # 5 MiB
        chunk_count_max = 10000

    # Unsure to have the minimum valid chunk size
    chunk_size = max(chunk_size_min, desired_chunk_size)

    # Compute the number of chunks
    chunk_count = file_size // chunk_size + (file_size % chunk_size > 0)

    # If the chunks count exceeds the maximum chunks count ...
    if chunk_count_max and chunk_count > chunk_count_max:
        # ... In that case, the chunk count will define the chunk size
        return chunk_partition(
            file_size, file_size // (chunk_count_max - 1), handler=handler
        )

    return chunk_count, chunk_size


def get_digest_algorithm(digest):
    # type: (Text) -> Optional[Text]

    # Available algorithms
    digesters = {
        32: "md5",
        40: "sha1",
        56: "sha224",
        64: "sha256",
        96: "sha384",
        128: "sha512",
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
        logger.warning("No valid hash algorithm found for digest %r", digest)

    return func


def guess_mimetype(filename):
    # type: (Text) -> Text
    """ Guess the mimetype of a given file. """
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        if sys.platform == "win32":
            # Patch bad Windows MIME types
            # See http://bugs.python.org/issue15207 and NXP-11660
            mime_type = WIN32_PATCHED_MIME_TYPES.get(mime_type, mime_type)
        return mime_type

    return "application/octet-stream"


def json_helper(obj):
    # type: (Any) -> Dict[Text, Any]
    return obj.to_json()


def log_chunk_details(chunk_count, chunk_size, uploaded_chunks, blob_size):
    # type: (int, int, List[int], int) -> None
    """Simple helper to log an chunked upload details about chunks data.

    :param chunk_count: the number of chunks
    :param chunk_size: the size of each chunks
    :param uploaded_chunks: the list of already uploaded chunks
    """
    if chunk_count <= 1 or logger.getEffectiveLevel() > logging.DEBUG:
        return

    uploaded_chunks_count = len(uploaded_chunks)
    uploaded_data_length = min(blob_size, chunk_size * uploaded_chunks_count)
    msg = (
        "Computed chunks count is {:,d}"
        "; chunks size is {:,d} bytes"
        "; uploaded chunks count is {:,d}"
        " => uploaded data so far is {:,d} bytes."
    )
    details = msg.format(
        chunk_count, chunk_size, uploaded_chunks_count, uploaded_data_length
    )
    logger.debug(details)


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
