# coding: utf-8

from requests import HTTPError


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
        if http_error:
            self.__dict__.update(http_error.__dict__)
        self.user_id = user_id
        self.message = str(self)

    def __str__(self):
        return '\'{!s}\' is not authorized to access {!s} with the provided credentials'.format(
            self.user_id.encode('utf-8'), self.response.url)


class UnavailableConvertor(Exception):
    """
    Exception for when a converter is registered but not
    available right now (e.g. not installed on the server).

    :param options: options passed to the conversion request
    """
    def __init__(self, options):
        self.options = options

    def __str__(self):
        return 'Conversion with options {!r} is not available'.format(self.options)
