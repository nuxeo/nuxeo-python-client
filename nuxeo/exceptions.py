# coding: utf-8
from requests import HTTPError

__all__ = ('InvalidBatchException', 'Unauthorized')


class InvalidBatchException(ValueError):
    pass


class Unauthorized(HTTPError):

    def __init__(self, server_url, user_id, code=403):
        self.server_url = server_url
        self.user_id = user_id
        self.code = code

    def __str__(self):
        return '{!r} is not authorized to access {!r} with the provided credentials'.format(
            self.user_id, self.server_url)
