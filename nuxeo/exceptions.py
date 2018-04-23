# coding: utf-8
from __future__ import unicode_literals

from .compat import get_text, text

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, Optional, Text
except ImportError:
    pass


class CorruptedFile(ValueError):
    """ Exception thrown when digests of a downloaded blob are different. """

    def __init__(self, filename, server_digest, local_digest):
        # type: (Text, Text, Text) -> None
        self.filename = filename
        self.server_digest = server_digest
        self.local_digest = local_digest

    def __repr__(self):
        # type: () -> Text
        err = ('Corrupted file {!r}: server digest '
               'is {!r}, local digest is {!r}')
        return err.format(self.filename, self.server_digest, self.local_digest)

    def __str__(self):
        # type: () -> Text
        return repr(self)


class EmptyFile(ValueError):
    """ Exception thrown when someone tries to upload an empty file. """

    def __init__(self, name):
        # type: (Text) -> None
        self.name = name

    def __repr__(self):
        # type: () -> Text
        return 'File {!r} is empty.'.format(self.name)

    def __str__(self):
        # type: () -> Text
        return repr(self)


class HTTPError(Exception):
    """ Exception thrown when the server returns an error. """
    _valid_properties = {
        'status': None,
        'message': None,
        'stacktrace': None
    }

    def __init__(self, **kwargs):
        # type: (Any) -> None
        for key, default in HTTPError._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    def __repr__(self):
        # type: () -> Text
        return '{} error: {}'.format(self.status, get_text(self.message))

    def __str__(self):
        # type: () -> Text
        return repr(self)

    @classmethod
    def parse(cls, json):
        # type: (Dict[Text, Any]) -> HTTPError
        """ Parse a JSON object into a model instance. """
        model = cls()

        for key, val in json.items():
            if key in cls._valid_properties:
                setattr(model, key, val)
        return model


class IncompleteRead(IOError):
    """ Response length doesn't match expected Content-Length. """

    def __init__(self, actual_length, expected_length):
        # type: (int, int) -> None
        self.actual = actual_length
        self.expected = expected_length

    def __repr__(self):
        # type: () -> Text
        return 'IncompleteRead({} bytes read, {} expected)'.format(
            self.actual, self.expected)

    def __str__(self):
        # type: () -> Text
        return repr(self)


class InvalidBatch(ValueError):
    """
    Exception thrown when accessing inexistant or deleted batches.
    """
    pass


class Unauthorized(HTTPError):
    """
    Exception thrown when the HTTPError code is 401 or 403.
    """
    pass


class UnavailableConvertor(Exception):
    """
    Exception thrown when a converter is registered but not
    available right now (e.g. not installed on the server).

    :param options: options passed to the conversion request
    """
    def __init__(self, options):
        # type: (Dict[Text, Any]) -> None
        self.options = options
        self.message = text(self)

    def __repr__(self):
        # type: () -> Text
        err = 'Conversion with options {!r} is not available'
        return err.format(self.options)

    def __str__(self):
        # type: () -> Text
        return repr(self)


class UploadError(OSError):
    """
    Exception thrown when an upload fails even after retries.
    """
    def __init__(self, name, chunk=None):
        # type: (Text, Optional[int]) -> None
        self.name = name
        self.chunk = chunk

    def __repr__(self):
        # type: () -> Text
        err = 'Unable to upload file {!r}'.format(self.name)
        if self.chunk:
            err = '{} (failed at chunk {})'.format(err, self.chunk)
        return err

    def __str__(self):
        # type: () -> Text
        return repr(self)
