# coding: utf-8
from __future__ import unicode_literals

from .compat import get_text, text

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, Text
except ImportError:
    pass


class CorruptedFile(ValueError):
    """ Exception thrown when digests of a downloaded blob are different. """

    def __init__(self, filename, server_digest, local_digest):
        self.filename = filename
        self.server_digest = server_digest
        self.local_digest = local_digest

    def __str__(self):
        err = 'Corrupted file {!r}: server digest is {!r}, local digest is {!r}'
        return err.format(self.filename, self.server_digest, self.local_digest)


class HTTPError(Exception):
    _valid_properties = {
        'status': None,
        'message': None,
        'stacktrace': None
    }

    def __init__(self, **kwargs):
        # type: (Any) -> None
        for key, default in HTTPError._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    def __str__(self):
        # type: () -> Text
        return '{} error: {}'.format(self.status, get_text(self.message))

    @classmethod
    def parse(cls, json):
        # type: (Dict[Text, Any]) -> HTTPError
        """ Parse a JSON object into a model instance. """
        model = cls()

        for key, val in json.items():
            if key in cls._valid_properties:
                setattr(model, key, val)
        return model


class InvalidBatch(ValueError):
    """
    Exception thrown when accessing inexistant or deleted batches.
    """
    pass


class Unauthorized(HTTPError):
    """
    Exception thrown when the HTTPError code is 401 or 403
    """
    pass


class UnavailableConvertor(Exception):
    """
    Exception for when a converter is registered but not
    available right now (e.g. not installed on the server).

    :param options: options passed to the conversion request
    """
    def __init__(self, options):
        # type: (Dict[Text, Any]) -> None
        self.options = options
        self.message = text(self)

    def __str__(self):
        # type: () -> Text
        return 'Conversion with options {!r} is not available'.format(self.options)
