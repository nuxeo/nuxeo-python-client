# coding: utf-8
from requests import HTTPError

__all__ = ('InvalidBatchException', 'Unauthorized')


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

    :param server_url: Nuxeo server URL
    :param user_id: ID of logged user
    :param code: HTTP error code (usually 401 or 403)
    """
    def __init__(self, server_url, user_id, code=403):
        self.server_url = server_url
        self.user_id = user_id
        self.code = code

    def __str__(self):
        return '{!r} is not authorized to access {!r} with the provided credentials'.format(
            self.user_id, self.server_url)
