# coding: utf-8
from __future__ import unicode_literals

import mimetypes
import sys

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


def json_helper(o):
    # type: (Any) -> Dict[Text, Any]
    if hasattr(o, 'to_json'):
        return o.to_json()
    raise TypeError(repr(o) + 'is not JSON serializable (no to_json() found)')


class SwapAttr:
    def __init__(self, o, attr, value):
        if not hasattr(o, attr):
            raise AttributeError()
        self.o = o
        self.attr = attr
        self.value = value
        self.old_value = getattr(o, attr)

    def __enter__(self):
        setattr(self.o, self.attr, self.value)

    def __exit__(self, *args):
        setattr(self.o, self.attr, self.old_value)
