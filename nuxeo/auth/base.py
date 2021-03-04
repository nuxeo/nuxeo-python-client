# coding: utf-8
from __future__ import unicode_literals

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from requests import Request
except ImportError:
    pass


class AuthBase(object):
    """Base class that all auth implementations derive from.
    Copied from requests.auth to add __slots__ capability.
    """

    __slots__ = ()

    def __call__(self, r):
        # type: (Request) -> Request
        raise NotImplementedError("Auth hooks must be callable.")
