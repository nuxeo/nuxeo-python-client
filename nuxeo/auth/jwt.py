# coding: utf-8
from __future__ import unicode_literals

from ..compat import get_bytes
from .base import AuthBase

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Text
        from requests import Request
except ImportError:
    pass


class JWTAuth(AuthBase):
    """ Attaches JSON Web Token Authentication to the given Request object. """

    __slots__ = ("token",)

    AUTHORIZATION = get_bytes("Authorization")

    def __init__(self, token):
        # type: (Text) -> None
        self.token = token

    def __eq__(self, other):
        # type: (object) -> bool
        return self.token == getattr(other, "token", None)

    def __ne__(self, other):
        # type: (object) -> bool
        return not self == other

    def __call__(self, r):
        # type: (Request) -> Request
        r.headers[self.AUTHORIZATION] = "Bearer " + self.token
        return r
