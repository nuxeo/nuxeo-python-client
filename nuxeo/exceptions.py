# coding: utf-8
from __future__ import unicode_literals

from .compat import text

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, Optional, Text  # noqa
except ImportError:
    pass


class NuxeoError(Exception):
    """ Mother class for all exceptions. """


class BadQuery(NuxeoError):
    """
    Exception thrown either by an operation failure:
        - when the command is not valid
        - on unexpected parameter
        - on missing required parameter
        - when a parameter has not the required type
    Or by any requests to the server with invalid data.
    """


class CorruptedFile(NuxeoError):
    """ Exception thrown when digests of a downloaded blob are different. """

    def __init__(self, filename, server_digest, local_digest):
        # type: (Text, Text, Text) -> None
        self.filename = filename
        self.server_digest = server_digest
        self.local_digest = local_digest

    def __repr__(self):
        # type: () -> Text
        err = ('CorruptedFile {!r}: server digest '
               'is {!r}, local digest is {!r}')
        return err.format(self.filename, self.server_digest, self.local_digest)

    def __str__(self):
        # type: () -> Text
        return repr(self)


class HTTPError(NuxeoError):
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
        return '%s(%d), error: %s, server trace: %s' % (
            type(self).__name__, self.status, self.message, self.stacktrace)

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


class InvalidBatch(NuxeoError):
    """ Exception thrown when accessing inexistant or deleted batches. """


class Unauthorized(HTTPError):
    """ Exception thrown when the HTTPError code is 401 or 403. """


class UnavailableConvertor(NuxeoError):
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
        return ('UnavailableConvertor: conversion with options {!r}'
                ' is not available').format(self.options)

    def __str__(self):
        # type: () -> Text
        return repr(self)


class UploadError(NuxeoError):
    """
    Exception thrown when an upload fails even after retries.
    """
    def __init__(self, name, chunk=None, info=None):
        # type: (Text, Optional[int], Optional[HTTPError]) -> None
        self.name = name
        self.chunk = chunk
        self.info = info

    def __repr__(self):
        # type: () -> Text
        err = 'UploadError: unable to upload file {!r}'.format(self.name)
        if self.chunk:
            err = '{} (failed at chunk {})'.format(err, self.chunk)
        if self.info:
            err = '{} (source: {})'.format(err, self.info)
        return err

    def __str__(self):
        # type: () -> Text
        return repr(self)
