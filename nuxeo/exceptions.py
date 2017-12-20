# coding: utf-8
from __future__ import unicode_literals

from requests import HTTPError

from .compat import text

try:
    from typing import Any, Dict, Optional, Text
except ImportError:
    pass


class InvalidBatchException(ValueError):
    """
    Exception thrown when accessing inexistant or deleted batches.
    """
    pass


class Unauthorized(HTTPError):
    """
    HTTPError-derived class.

    Used for filtering purposes so the errors due to lack of
    permissions don't get lost among the others.

    :param user_id: ID of logged user
    :param http_error: The HTTPError raised by the request
    """
    def __init__(self, user_id, http_error=None):
        # type: (Text, Optional[HTTPError]) -> None
        if http_error:
            self.__dict__.update(http_error.__dict__)
        self.user_id = user_id
        self.message = text(self)

    def __str__(self):
        # type: () -> Text
        return '\'{!s}\' is not authorized to access {!s} with the provided credentials'.format(
            self.user_id, self.response.url)


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
