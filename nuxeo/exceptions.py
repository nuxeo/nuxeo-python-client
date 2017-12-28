# coding: utf-8
from __future__ import unicode_literals

from .compat import text, get_text


class HTTPError(Exception):
    _valid_properties = {
        'status': None,
        'message': None,
        'stacktrace': None
    }

    def __init__(self, **kwargs):
        for key, default in HTTPError._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    def __str__(self):
        return '{} error: {}'.format(self.status, get_text(self.message))

    @classmethod
    def parse(cls, json):
        """ Parse a JSON object into a model instance. """
        model = cls()

        for key, val in json.items():
            if key in cls._valid_properties:
                setattr(model, key, val)
        return model


class Unauthorized(HTTPError):
    pass


class InvalidBatch(ValueError):
    """
       Exception thrown when accessing inexistant or deleted batches.
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
