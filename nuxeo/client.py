# coding: utf-8
import atexit
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from warnings import warn

import requests
from requests.adapters import HTTPAdapter
from urllib3 import __version__ as urllib3_version
from urllib3.util.retry import Retry
from urllib.parse import urlparse
from . import (
    __version__,
    comments,
    directories,
    documents,
    groups,
    operations,
    tasks,
    uploads,
    users,
    workflows,
)
from .auth.base import AuthBase
from .auth import BasicAuth, TokenAuth
from .constants import (
    CHUNK_SIZE,
    DEFAULT_API_PATH,
    DEFAULT_APP_NAME,
    DEFAULT_URL,
    IDEMPOTENCY_KEY,
    MAX_RETRY,
    RETRY_BACKOFF_FACTOR,
    RETRY_METHODS,
    RETRY_STATUS_CODES,
    TIMEOUT_CONNECT,
    TIMEOUT_READ,
)
from .exceptions import (
    BadQuery,
    Conflict,
    Forbidden,
    HTTPError,
    OngoingRequestError,
    Unauthorized,
)
from .tcp import TCPKeepAliveHTTPSAdapter
from .utils import json_helper, log_response

AuthType = Optional[Union[Tuple[str, str], AuthBase]]
logger = logging.getLogger(__name__)

if urllib3_version < "1.26.0":
    DEFAULT_RETRY = Retry(
        total=MAX_RETRY,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        method_whitelist=RETRY_METHODS,
        status_forcelist=RETRY_STATUS_CODES,
        raise_on_status=False,
    )
else:
    DEFAULT_RETRY = Retry(
        total=MAX_RETRY,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        allowed_methods=RETRY_METHODS,
        status_forcelist=RETRY_STATUS_CODES,
        raise_on_status=False,
    )

# Custom exception to raise based on the HTTP status code
# (default will be HTTPError)
HTTP_ERROR = {
    requests.codes.conflict: Conflict,
    requests.codes.forbidden: Forbidden,
    requests.codes.unauthorized: Unauthorized,
}


class NuxeoClient(object):
    """
    The HTTP client used by Nuxeo.

    :param auth: An authentication object passed to Requests
    :param host: The url of the Nuxeo Platform
    :param api_path: The API path appended to the host url
    :param chunk_size: The size of the chunks for blob download
    :param kwargs: kwargs passed to :func:`NuxeoClient.request`
    """

    # Cache mapping username -> generated UID.
    # Populated lazily on first encounter via resolve_uid / resolve_username.
    userid_mapper = {}  # type: Dict[str, str]

    # --- Known param keys that carry a username value in REQUESTS ---
    # These keys, when found inside the ``params`` dict sent to the server
    # (either as URL query parameters or inside the automation payload),
    # contain a username string that must be translated to a generated UID.
    _USERNAME_REQUEST_KEYS = frozenset({
        "username",        # Document.AddPermission, User.Invite, …
        "user",            # Document.RemovePermission, …
        "users",           # bulk user references
        "userId",          # Task queries, …
        "actors",          # Task delegate / reassign (may be a list)
        "delegatedActors",  # Task delegate (may be a list)
    })

    # --- Known response keys whose value is a username / list of usernames ---
    # After the server starts returning generated UIDs in these fields, we
    # translate them back to usernames so callers (e.g. Drive) see no change.
    _USERNAME_RESPONSE_KEYS = frozenset({
        "lockOwner",
        "dc:lastContributor",
        "dc:creator",
        "dc:contributors",   # list of usernames
        "lastContributor",   # filesystem-item style
        "principalName",     # audit entries
        "actors",            # task actors (list, prefixed "user:…")
        "initiator",         # workflow initiator
        "author",            # comment author
        "creator",           # some simplified payloads
    })

    def __init__(
        self,
        auth=None,  # type: AuthType
        host=DEFAULT_URL,  # type: str
        api_path=DEFAULT_API_PATH,  # type: str
        chunk_size=CHUNK_SIZE,  # type: int
        **kwargs,  # type: Any
    ):
        # type: (...) -> None
        self.auth = BasicAuth(*auth) if isinstance(auth, tuple) else auth
        self.host = host
        self.api_path = api_path
        self.chunk_size = chunk_size

        version = kwargs.pop("version", "")
        app_name = kwargs.pop("app_name", DEFAULT_APP_NAME)
        self.headers = {
            "X-Application-Name": app_name,
            "X-Client-Version": version,
            "User-Agent": f"{app_name}/{version}",
            "Accept": "application/json, */*",
        }

        self.schemas = kwargs.get("schemas", "*")
        self.repository = kwargs.pop("repository", "default")
        self._session = requests.sessions.Session()
        self._session.hooks["response"] = [log_response]
        cookies = kwargs.pop("cookies", None)
        if cookies:
            self._session.cookies = cookies
        self._session.stream = True
        self.client_kwargs = kwargs

        self.ssl_verify_needed = kwargs.get("verify", True)

        atexit.register(self.on_exit)

        # Cache for the server information
        self._server_info = None

        # Ensure the host is well formatted
        if not self.host.endswith("/"):
            self.host += "/"

        # The retry adapter
        self.retries = kwargs.pop("retries", None) or DEFAULT_RETRY

        # Install the retries mecanism
        self.enable_retry()

    def __repr__(self):
        # type: () -> str
        return f"{type(self).__name__}<host={self.host!r}, version={self.server_version!r}>"

    def __str__(self):
        # type: () -> str
        return repr(self)

    def on_exit(self):
        # type: () -> None
        self._session.close()

    def enable_retry(self):
        # type: () -> None
        """Set a max retry for all connection errors with an adaptative backoff."""
        self._session.mount(
            "https://", TCPKeepAliveHTTPSAdapter(max_retries=self.retries)
        )
        self._session.mount("http://", HTTPAdapter(max_retries=self.retries))

    def disable_retry(self):
        # type: () -> None
        """
        Restore default mount points to disable the eventual retry
        adapters set with .enable_retry().
        """
        self._session.close()
        self._session.mount("https://", TCPKeepAliveHTTPSAdapter())
        self._session.mount("http://", HTTPAdapter())

    # ------------------------------------------------------------------
    #  Username ↔ Generated-UID mapping
    # ------------------------------------------------------------------

    def _fetch_uid_for_username(self, username):
        # type: (str) -> str
        """
        Call the server to obtain the generated UID for *username*.

        .. note::
            Dummy placeholder — returns a deterministic fake UID.
            Replace the body once the actual server endpoint is known.
        """
        dummy_uid = f"uid-{username}"
        logger.debug("_fetch_uid_for_username(%r) -> %r  [DUMMY]", username, dummy_uid)
        return dummy_uid

    def _fetch_username_for_uid(self, uid):
        # type: (str) -> str
        """
        Call the server to obtain the username for a generated *uid*.

        .. note::
            Dummy placeholder — strips the ``uid-`` prefix.
            Replace the body once the actual server endpoint is known.
        """
        dummy_username = uid.replace("uid-", "", 1) if uid.startswith("uid-") else uid
        logger.debug("_fetch_username_for_uid(%r) -> %r  [DUMMY]", uid, dummy_username)
        return dummy_username

    def resolve_uid(self, username):
        # type: (str) -> str
        """Return the generated UID for *username*, using cache first."""
        if username in self.userid_mapper:
            return self.userid_mapper[username]

        uid = self._fetch_uid_for_username(username)
        self.userid_mapper[username] = uid
        return uid

    def resolve_username(self, uid):
        # type: (str) -> str
        """Return the username for a generated *uid*, using reverse cache first."""
        for username, mapped_uid in self.userid_mapper.items():
            if mapped_uid == uid:
                return username

        username = self._fetch_username_for_uid(uid)
        self.userid_mapper[username] = uid
        return username

    # ------------------------------------------------------------------
    #  Request / Response translation helpers
    # ------------------------------------------------------------------

    def _translate_request_params(self, params):
        # type: (Dict[str, Any]) -> Dict[str, Any]
        """
        Scan *params* for known username-carrying keys and replace each
        username value with its corresponding generated UID.

        Returns a **new** dict — the original is never mutated.
        """
        if not params:
            return params

        translated = {}
        for key, value in params.items():
            if key not in self._USERNAME_REQUEST_KEYS:
                translated[key] = value
                continue

            if isinstance(value, str):
                translated[key] = self._translate_single_username_to_uid(value)
            elif isinstance(value, list):
                translated[key] = [
                    self._translate_single_username_to_uid(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                translated[key] = value
        return translated

    def _translate_single_username_to_uid(self, value):
        # type: (str) -> str
        """Translate a single username string to its UID.

        Supports prefixed values like ``"user:john"``."""
        if ":" in value:
            prefix, name = value.split(":", 1)
            return f"{prefix}:{self.resolve_uid(name)}"
        return self.resolve_uid(value)

    def _translate_response(self, data):
        # type: (Any) -> Any
        """
        Recursively walk *data* (dict / list) and replace generated UIDs
        with usernames in every field whose key is in
        ``_USERNAME_RESPONSE_KEYS``.

        Mutates in-place for efficiency.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key in self._USERNAME_RESPONSE_KEYS:
                    data[key] = self._translate_uid_value_to_username(value)
                elif isinstance(value, (dict, list)):
                    self._translate_response(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._translate_response(item)
        return data

    def _translate_uid_value_to_username(self, value):
        # type: (Any) -> Any
        """Translate a single UID string (or list of UIDs) back to username(s).

        Supports prefixed values like ``"user:uid-john"``."""
        if isinstance(value, str):
            if ":" in value:
                prefix, uid_part = value.split(":", 1)
                return f"{prefix}:{self.resolve_username(uid_part)}"
            return self.resolve_username(value)
        elif isinstance(value, list):
            return [self._translate_uid_value_to_username(v) for v in value]
        return value

    def query(
        self,
        query,  # type: str
        params=None,  # type: Dict[str, Any]
    ):
        """
        Query the server with the specified NXQL query.
        Additional qery parameters can be set via the `params` argument:

            >>> nuxeo.client.query('NXSQL query', params={'properties': '*'})

        You can find what parameters to tweak under the `Repository.Query`
        operation details.
        """

        data = {"query": query}
        if params:
            data.update(params)

        url = f"{self.api_path}/search/lang/NXQL/execute"
        return self.request("GET", url, params=data).json()

    def set(self, repository=None, schemas=None):
        # type: (Optional[str], Optional[str]) -> NuxeoClient
        """
        Set the repository and/or the schemas for the requests.

        :return: The client instance after adding the settings
        """
        if repository:
            self.repository = repository

        if schemas:
            if isinstance(schemas, list):
                schemas = ",".join(schemas)
            self.schemas = schemas

        return self

    def request(
        self,
        method,  # type: str
        path,  # type: str
        headers=None,  # type: Optional[Dict[str, str]]
        data=None,  # type: Optional[Any]
        raw=False,  # type: bool
        ssl_verify=True,  # type: bool
        **kwargs,  # type: Any
    ):
        # type: (...) -> Union[requests.Response, Any]
        """
        Send a request to the Nuxeo server.

        :param method: the HTTP method
        :param path: the path to append to the host
        :param headers: the headers for the HTTP request
        :param data: data to put in the body
        :param raw: if True, don't parse the data to JSON
        :param kwargs: other parameters accepted by
               :func:`requests.request`
        :return: the HTTP response
        """
        if method not in (
            "GET",
            "HEAD",
            "POST",
            "PUT",
            "DELETE",
            "CONNECT",
            "OPTIONS",
            "TRACE",
        ):
            raise BadQuery("method parameter is not a valid HTTP method.")

        # Construct the full URL without double slashes
        url = self.host + path.lstrip("/")
        if "adapter" in kwargs:
            url = f"{url}/@{kwargs.pop('adapter')}"

        kwargs.update(self.client_kwargs)

        # --- Translate URL query params (e.g. ?userId=alice) -----------
        if "params" in kwargs and isinstance(kwargs["params"], dict):
            kwargs["params"] = self._translate_request_params(kwargs["params"])

        # Set the default value to `object` to allow someone
        # to set `default` to `None`.
        if kwargs.get("timeout", object) is object:
            kwargs["timeout"] = (TIMEOUT_CONNECT, TIMEOUT_READ)

        headers = headers or {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = kwargs.pop("content_type", "application/json")
        headers.update(
            {"X-NXDocumentProperties": self.schemas, "X-NXRepository": self.repository}
        )
        enrichers = kwargs.pop("enrichers", None)
        if enrichers:
            headers["enrichers-document"] = ", ".join(enrichers)

        headers.update(self.headers)
        self._check_headers_and_params_format(headers, kwargs.get("params") or {})

        if data and not isinstance(data, bytes) and not raw:
            data = json.dumps(data, default=json_helper)

        # Set the default value to `object` to allow someone
        # to set `default` to `None`.
        default = kwargs.pop("default", object)

        # Allow to pass a custom authentication class
        auth = kwargs.pop("auth", None) or self.auth

        _kwargs = {k: v for k, v in kwargs.items() if k != "params"}
        logged_params = kwargs.get("params", {} if raw else data)
        logger.debug(
            (
                f"Calling {method} {url!r} with headers={headers!r},"
                f" params={logged_params!r}, kwargs={_kwargs!r}"
            )
        )

        exc = None

        if not self.ssl_verify_needed:
            ssl_verify = False

        if "verify" in kwargs:
            if not kwargs["verify"]:
                ssl_verify = False
            kwargs.pop("verify")

        try:
            resp = self._session.request(
                method,
                url,
                headers=headers,
                auth=auth,
                data=data,
                allow_redirects=False,
                verify=ssl_verify,
                **kwargs,
            )
            if resp.status_code in range(301, 309):
                try:
                    redirect_url = resp.headers["Location"]
                except Exception:
                    redirect_url = ""
                hostname = urlparse(redirect_url).hostname or ""
                # Safely check if hostname is a subdomain of amazonaws.com
                if hostname == "amazonaws.com" or hostname.endswith(".amazonaws.com"):
                    resp = requests.get(
                        url=resp.headers["Location"],
                        headers=resp.headers,
                        data=data,
                        allow_redirects=True,
                        verify=ssl_verify,
                        **kwargs,
                    )
                else:
                    resp = self._session.request(
                        method,
                        url,
                        headers=headers,
                        auth=auth,
                        data=data,
                        verify=ssl_verify,
                        **kwargs,
                    )
            resp.raise_for_status()
        except Exception as exc:
            if default is object:
                raise self._handle_error(exc)
            resp = default
        finally:
            # Explicitly break a reference cycle
            exc = None
            del exc

        # --- Wrap response so .json() auto-translates UIDs → usernames ---
        if isinstance(resp, requests.Response) and self.userid_mapper is not None:
            _original_json = resp.json

            def _translated_json(**kw):
                data = _original_json(**kw)
                return self._translate_response(data)

            resp.json = _translated_json  # type: ignore[assignment]

        return resp

    def _check_headers_and_params_format(self, headers, params):
        # type: (Dict[str, Any], Dict[str, Any]) -> None
        """Check headers and params keys for dots or underscores and throw a warning if one is found."""

        msg = "{!r} {} should not contain '_' nor '.'. Replace with '-' to get rid of that warning."

        for key in headers.keys():
            if "_" in key or "." in key:
                warn(msg.format(key, "header"), DeprecationWarning, 2)

        if not isinstance(params, dict):
            return
        for key in params.keys():
            if "_" in key or "." in key:
                warn(msg.format(key, "param"), DeprecationWarning, 2)

    def request_auth_token(
        self,
        device_id,  # type: str
        permission,  # type: str
        app_name=DEFAULT_APP_NAME,  # type: str
        device=None,  # type: Optional[str]
        revoke=False,  # type: bool
        ssl_verify=True,  # type: bool
    ):
        # type: (...) -> str
        """
        Request a token for the user.
        It should only be used if you want to get a Nuxeo token from a Basic Auth.

        :param device_id: device identifier
        :param permission: read/write permissions
        :param app_name: application name
        :param device: optional device description
        :param revoke: revoke the token
        """
        auth = TokenAuth("")
        token = auth.request_token(
            self,
            device_id,
            permission,
            app_name=app_name,
            device=device,
            revoke=revoke,
            auth=self.auth,
            ssl_verify=ssl_verify,
        )

        # Use the (potentially re-newed) token from now on
        if not revoke:
            self.auth = auth
        return token

    def is_reachable(self):
        # type: () -> bool
        """Check if the Nuxeo Platform is reachable."""
        response = self.request("GET", "runningstatus", default=False)
        if isinstance(response, requests.Response):
            return response.ok
        else:
            return bool(response)

    def server_info(self, force=False, ssl_verify=True):
        # type: (bool, bool) -> Dict[str, str]
        """
        Retreive server information.

        :param bool force: Force information renewal.
        """
        if force or self._server_info is None:
            try:
                response = self.request("GET", "json/cmis", ssl_verify=ssl_verify)
                self._server_info = response.json()["default"]
            except Exception:
                logger.warning(
                    "Invalid response data when called server_info()", exc_info=True
                )
        return self._server_info

    @property
    def server_version(self, ssl_verify=True):
        # type: (bool) -> str
        """Return the server version or "unknown"."""
        try:
            return self.server_info(ssl_verify)["productVersion"]
        except Exception:
            return "unknown"

    @staticmethod
    def _handle_error(error):
        # type: (Exception) -> Exception
        """
        Log error and handle raise.

        :param error: The error to handle
        """
        if not isinstance(error, requests.HTTPError):
            return error

        response = error.response
        error_data = {}
        try:
            error_data.update(response.json())
        except ValueError:
            error_data["message"] = response.content
        finally:
            error_data["status"] = response.status_code
            if not error_data.get("message", ""):
                error_data["message"] = response.reason

        status = error_data["status"]
        request_uid = response.headers.get(IDEMPOTENCY_KEY, "")
        if status == 409 and request_uid:
            return OngoingRequestError(request_uid)
        return HTTP_ERROR.get(status, HTTPError).parse(error_data)


class Nuxeo(object):
    """
    Instantiate the client and all the API Endpoints.

    :param auth: the authenticator
    :param host: the host URL
    :param app_name: the name of the application using the client
    :param client: the client class
    :param kwargs: any other argument to forward to every requests calls
    """

    def __init__(
        self,
        auth=None,  # type: Optional[Tuple[str, str]]
        host=DEFAULT_URL,  # type: str
        app_name=DEFAULT_APP_NAME,  # type: str
        version=__version__,  # type: str
        verify=True,  # bool
        client=NuxeoClient,  # type: Type[NuxeoClient]
        **kwargs,  # type: Any
    ):
        # type: (...) -> None
        kwargs["verify"] = verify
        self.client = client(
            auth, host=host, app_name=app_name, version=version, **kwargs
        )
        self.comments = comments.API(self.client)
        self.operations = operations.API(self.client)
        self.directories = directories.API(self.client)
        self.groups = groups.API(self.client)
        self.tasks = tasks.API(self.client)
        self.uploads = uploads.API(self.client)
        self.users = users.API(self.client)
        self.workflows = workflows.API(self.client, self.tasks)
        self.documents = documents.API(
            self.client, self.operations, self.workflows, self.comments
        )

    def __repr__(self):
        # type: () -> str
        return f"{type(self).__name__}<version={__version__!r}, client={self.client!r}>"

    def __str__(self):
        # type: () -> str
        return repr(self)

    def can_use(self, operation):
        # type: (str) -> str
        """Return a boolean to let the caller know if the given *operation* can be used."""
        return operation in self.operations.operations
