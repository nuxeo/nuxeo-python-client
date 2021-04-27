# coding: utf-8
from __future__ import unicode_literals

from time import time

from authlib.common.security import generate_token
from authlib.integrations.base_client.errors import AuthlibBaseError
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from ..compat import get_bytes
from ..exceptions import OAuth2Error
from ..utils import log_response
from .base import AuthBase

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Callable, Dict, Optional, Text, Tuple
        from requests import Request

        Token = Dict[str, Any]
except ImportError:
    pass


DEFAULT_AUTHORIZATION_ENDPOINT = "oauth2/authorize"
DEFAULT_TOKEN_ENDPOINT = "oauth2/token"


class OAuth2(AuthBase):
    """OAuth2 mechanism."""

    __slots__ = (
        "token",
        "_authorization_endpoint",
        "_client",
        "_host",
        "_token_endpoint",
        "_token_header",
    )

    AUTHORIZATION = get_bytes("Authorization")
    GRANT_AUTHORIZATION_CODE = "authorization_code"

    def __init__(
        self,
        host,
        client_secret=None,
        client_id=None,
        token=None,
        authorization_endpoint=None,
        token_endpoint=None,
    ):
        # type: (Text, Optional[Text], Optional[Text], Optional[Token], Optional[Text], Optional[Text]) -> None
        if not host.endswith("/"):
            host += "/"
        self._host = host
        self._client = OAuth2Session(client_id=client_id, client_secret=client_secret)
        self._client.session.hooks["response"] = [log_response]
        self._token_header = ""
        self.token = {}  # type: Token
        if token:
            self.set_token(token)

        # Allow to pass custom endpoints (not handled by the platform)
        auth_endpoint = authorization_endpoint or DEFAULT_AUTHORIZATION_ENDPOINT
        token_endpoint = token_endpoint or DEFAULT_TOKEN_ENDPOINT
        if not auth_endpoint.startswith("https://"):
            auth_endpoint = self._host + auth_endpoint
        self._authorization_endpoint = auth_endpoint
        if not token_endpoint.startswith("https://"):
            token_endpoint = self._host + token_endpoint
        self._token_endpoint = token_endpoint

    def _request(self, method, *args, **kwargs):
        # type: (Callable, Any, Any) -> Any
        """Make a request with the OAuthlib client and shadow exceptions."""
        try:
            return method(*args, **kwargs)
        except AuthlibBaseError as exc:
            # TODO NXPY-129: Use raise ... from None
            raise OAuth2Error(exc.description)

    def token_is_expired(self):
        # type: () -> bool
        """Check whenever the current token is expired or not."""
        return self.token and self.token["expires_at"] < time()

    def create_authorization_url(self, **kwargs):
        # type: (Any) -> Tuple[str, str, str]
        """Create the authorization URL.
        Additionnal *kwargs* are passed to the underlying level.
        """
        code_verifier = generate_token(48)
        code_challenge = create_s256_code_challenge(code_verifier)
        uri, state = self._request(
            self._client.create_authorization_url,
            self._authorization_endpoint,
            code_challenge=code_challenge,
            code_challenge_method="S256",
            **kwargs
        )
        return uri, state, code_verifier

    def request_token(self, **kwargs):
        # type: (Any) -> Token
        """Do request for a token.
        The *code_verifier* kwarg is required in any cases.
        Other kwargs can be a combination of either:
            1. *authorization_response* or;
            2. *code* and *state*.
        """
        token = self._request(
            self._client.fetch_token,
            self._token_endpoint,
            grant_type=self.GRANT_AUTHORIZATION_CODE,
            **kwargs
        )
        self.set_token(token)
        return token

    def refresh_token(self):
        # type: () -> Token
        """Do refresh the current token using the *refresh_token*."""
        token = self._request(
            self._client.refresh_token,
            self._token_endpoint,
            self.token["refresh_token"],
        )
        self.set_token(token)
        return token

    def set_token(self, token):
        # type: (Token) -> None
        """Apply the given *token*."""
        self.token = token
        self._token_header = token["token_type"].title() + " " + token["access_token"]

    def __eq__(self, other):
        # type: (object) -> bool
        return self.token == getattr(other, "token", None)

    def __ne__(self, other):
        # type: (object) -> bool
        return not self == other

    def __call__(self, r):
        # type: (Request) -> Request
        if self.token_is_expired():
            self.refresh_token()

        r.headers[self.AUTHORIZATION] = self._token_header
        return r
