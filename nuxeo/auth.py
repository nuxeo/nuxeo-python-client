# coding: utf-8
from __future__ import unicode_literals

from requests.auth import AuthBase

from .compat import get_bytes

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Text  # noqa
        from requests import Request  # noqa
except ImportError:
    pass


class TokenAuth(AuthBase):
    """ Attaches Nuxeo Token Authentication to the given Request object. """

    def __init__(self, token):
        # type: (Text) -> None
        self.token = token

    def __eq__(self, other):
        # type: (object) -> bool
        return self.token == getattr(other, 'token', None)

    def __ne__(self, other):
        # type: (object) -> bool
        return not self == other

    def __call__(self, r):
        # type: (Request) -> Request
        r.headers[get_bytes('X-Authentication-Token')] = self.token
        return r
