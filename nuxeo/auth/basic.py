# coding: utf-8
from __future__ import unicode_literals
import base64

from ..compat import get_bytes, get_text
from .base import AuthBase

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Text
        from requests import Request
except ImportError:
    pass


class BasicAuth(AuthBase):
    """ Attaches a simple Basic Authentication to the given Request object. """

    __slots__ = ("username", "password", "_token_header")

    AUTHORIZATION = get_bytes("Authorization")

    def __init__(self, username, password):
        # type: (Text, Text) -> None
        self.username = username
        self.password = password
        self.set_token(password)

    def set_token(self, token):
        # type: (Text) -> None
        """Apply the given *token*."""
        self.password = token
        self._token_header = "Basic " + get_text(
            base64.b64encode(get_bytes(self.username + ":" + self.password))
        )

    def __eq__(self, other):
        # type: (object) -> bool
        return all(
            [
                self.username == getattr(other, "username", None),
                self.password == getattr(other, "password", None),
            ]
        )

    def __ne__(self, other):
        # type: (object) -> bool
        return not self == other

    def __call__(self, r):
        # type: (Request) -> Request
        r.headers[self.AUTHORIZATION] = self._token_header
        return r
