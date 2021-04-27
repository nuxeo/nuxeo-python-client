# coding: utf-8
from __future__ import unicode_literals

from ..constants import DEFAULT_APP_NAME
from ..compat import get_bytes, text
from .base import AuthBase

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Dict, Optional, Text
        from requests import Request

        Token = Dict[str, Any]
except ImportError:
    pass


class TokenAuth(AuthBase):
    """ Attaches Nuxeo Token Authentication to the given Request object. """

    __slots__ = ("token",)

    HEADER_TOKEN = get_bytes("X-Authentication-Token")

    def __init__(self, token):
        # type: (Text) -> None
        self.token = token

    def request_token(
        self,
        client,
        device_id,  # type: Text
        permission,  # type: Text
        app_name=DEFAULT_APP_NAME,  # type: Text
        device=None,  # type: Optional[Text]
        revoke=False,  # type: bool
        auth=None,
    ):
        # type: (...) -> Token
        """
        Request a token.

        :param device_id: device identifier
        :param permission: read/write permissions
        :param app_name: application name
        :param device: optional device description
        :param revoke: revoke the token
        """

        params = {
            "deviceId": device_id,
            "applicationName": app_name,
            "permission": permission,
            "revoke": text(revoke).lower(),
        }
        if device:
            params["deviceDescription"] = device

        path = "authentication/token"
        token = client.request("GET", path, params=params, auth=auth).text
        token = "" if (revoke or "\n" in token) else token
        self.set_token(token)
        return token

    def set_token(self, token):
        # type: (Token) -> None
        """Apply the given *token*."""
        self.token = token

    def __eq__(self, other):
        # type: (object) -> bool
        return self.token == getattr(other, "token", None)

    def __ne__(self, other):
        # type: (object) -> bool
        return not self == other

    def __call__(self, r):
        # type: (Request) -> Request
        r.headers[self.HEADER_TOKEN] = self.token
        return r
