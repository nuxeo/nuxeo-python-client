# coding: utf-8
from __future__ import unicode_literals

import atexit
import json
import logging
from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter

from . import (
    __version__,
    directories,
    documents,
    groups,
    operations,
    tasks,
    uploads,
    users,
    workflows,
)
from .auth import TokenAuth
from .compat import text
from .constants import (
    CHUNK_SIZE,
    DEFAULT_API_PATH,
    DEFAULT_APP_NAME,
    DEFAULT_URL,
    MAX_RETRY,
    RETRY_BACKOFF_FACTOR,
    RETRY_METHODS,
    RETRY_STATUS_CODES,
    TIMEOUT_CONNECT,
    TIMEOUT_READ,
)
from .exceptions import BadQuery, Forbidden, HTTPError, Unauthorized
from .utils import json_helper

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Dict, Optional, Text, Tuple, Type, Union  # noqa
        from requests.auth import AuthBase  # noqa

        AuthType = Optional[Union[Tuple[Text, Text], AuthBase]]
except ImportError:
    pass

logger = logging.getLogger(__name__)


# Custom exception to raise based on the HTTP status code
# (default will be HTTPError)
HTTP_ERROR = {
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

    def __init__(
        self,
        auth=None,  # type: AuthType
        host=DEFAULT_URL,  # type: Text
        api_path=DEFAULT_API_PATH,  # type: Text
        chunk_size=CHUNK_SIZE,  # type: int
        **kwargs  # type: Any
    ):
        # type: (...) -> None
        self.auth = auth
        self.host = host
        self.api_path = api_path
        self.chunk_size = chunk_size

        version = kwargs.pop("version", "")
        app_name = kwargs.pop("app_name", DEFAULT_APP_NAME)
        self.headers = {
            "X-Application-Name": app_name,
            "X-Client-Version": version,
            "User-Agent": app_name + "/" + version,
            "Accept": "application/json, */*",
        }
        self.schemas = kwargs.get("schemas", "*")
        self.repository = kwargs.pop("repository", "default")
        self._session = requests.sessions.Session()
        cookies = kwargs.pop("cookies", None)
        if cookies:
            self._session.cookies = cookies
        self._session.stream = True
        self.client_kwargs = kwargs
        atexit.register(self.on_exit)

        # Cache for the server information
        self._server_info = None

        # Ensure the host is well formatted
        if not self.host.endswith("/"):
            self.host += "/"

        # The retry adapter
        self.retries = Retry(
            total=MAX_RETRY,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            method_whitelist=RETRY_METHODS,
            status_forcelist=RETRY_STATUS_CODES,
        )

        # Install the retries mecanism
        self.enable_retry()

    def __repr__(self):
        # type: () -> Text
        fmt = "{name}<host={cls.host!r}, version={cls.server_version!r}>"
        return fmt.format(name=type(self).__name__, cls=self)

    def __str__(self):
        # type: () -> Text
        return repr(self)

    def on_exit(self):
        # type: () -> None
        self._session.close()

    def enable_retry(self):
        # type: () -> None
        """ Set a max retry for all connection errors with an adaptative backoff. """
        self._session.mount("https://", HTTPAdapter(max_retries=self.retries))
        self._session.mount("http://", HTTPAdapter(max_retries=self.retries))

    def disable_retry(self):
        # type: () -> None
        """
        Restore default mount points to disable the eventual retry
        adapters set with .enable_retry().
        """
        self._session.mount("https://", HTTPAdapter())
        self._session.mount("http://", HTTPAdapter())

    def query(
        self,
        query,  # type: Text
        params=None,  # type: Dict[Text, Any]
    ):
        """
        Query the server with the specified NXQL query.
        Additional qery parameters can be set via the `params` argument:

            >>> nuxeo.client.query('SQL query', params={'properties': '*'})

        You can find what parameters to tweak under the `Repository.Query`
        operation details.
        """

        data = {"query": query}
        if params:
            data.update(params)

        url = self.api_path + "/search/lang/NXQL/execute"
        return self.request("GET", url, params=data).json()

    def set(self, repository=None, schemas=None):
        # type: (Optional[Text], Optional[Text]) -> NuxeoClient
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
        method,  # type: Text
        path,  # type: Text
        headers=None,  # type: Optional[Dict[Text, Text]]
        data=None,  # type: Optional[Any]
        raw=False,  # type: bool
        **kwargs  # type: Any
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
            url = "{}/@{}".format(url, kwargs.pop("adapter"))

        kwargs.update(self.client_kwargs)

        if "timeout" not in kwargs:
            kwargs["timeout"] = (TIMEOUT_CONNECT, TIMEOUT_READ)

        headers = headers or {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = kwargs.pop("content_type", "application/json")
        headers.update(
            {"X-NXDocumentProperties": self.schemas, "X-NXRepository": self.repository}
        )
        enrichers = kwargs.pop("enrichers", None)
        if enrichers:
            headers["X-NXenrichers.document"] = ", ".join(enrichers)

        headers.update(self.headers)

        if data and not isinstance(data, bytes) and not raw:
            data = json.dumps(data, default=json_helper)

        # Set the default value to `object` to allow someone
        # to set `default` to `None`.
        default = kwargs.pop("default", object)

        logger.debug(
            ("Calling {!r} with headers={!r}, params={!r} and cookies={!r}").format(
                url,
                headers,
                kwargs.get("params", data if not raw else {}),
                self._session.cookies,
            )
        )

        exc = None
        try:
            resp = self._session.request(
                method, url, headers=headers, auth=self.auth, data=data, **kwargs
            )
            resp.raise_for_status()
        except Exception as exc:
            if default is object:
                raise self._handle_error(exc)
            resp = default
        else:
            # No need to do more work if nobody will see it
            if logger.getEffectiveLevel() <= logging.DEBUG:
                self._log_response(resp, self.chunk_size)
        finally:
            # Explicitly break a reference cycle
            exc = None
            del exc

        return resp

    def request_auth_token(
        self,
        device_id,  # type: Text
        permission,  # type: Text
        app_name=DEFAULT_APP_NAME,  # type: Text
        device=None,  # type: Optional[Text]
        revoke=False,  # type: bool
    ):
        # type: (...) -> Text
        """
        Request a token for the user.

        :param device_id: device identifier
        :param permission: read/write permissions
        :param app_name: application name
        :param device: optional device description
        :param revoke: revoke the token
        """

        parameters = {
            "deviceId": device_id,
            "applicationName": app_name,
            "permission": permission,
            "revoke": text(revoke).lower(),
        }
        if device:
            parameters["deviceDescription"] = device

        path = "authentication/token"
        token = self.request("GET", path, params=parameters).text

        # Use the (potentially re-newed) token from now on
        if not revoke:
            self.auth = TokenAuth(token)
        return token

    def is_reachable(self):
        # type: () -> bool
        """ Check if the Nuxeo Platform is reachable. """
        response = self.request("GET", "runningstatus", default=False)
        if isinstance(response, requests.Response):
            return response.ok
        else:
            return bool(response)

    def server_info(self, force=False):
        # type: (bool) -> Dict[Text, Text]
        """
        Retreive server information.

        :param bool force: Force information renewal.
        """

        if force or self._server_info is None:
            response = self.request("GET", "json/cmis", default={})
            if isinstance(response, requests.Response):
                info = response.json()["default"]
            else:
                info = response
            self._server_info = info
        return self._server_info

    @property
    def server_version(self):
        # type: () -> Text
        """ Return the server version. """
        return self.server_info().get("productVersion", "")

    @staticmethod
    def _handle_error(error):
        # type: (Exception) -> Exception
        """
        Log error and handle raise.

        :param error: The error to handle
        """
        if isinstance(error, requests.HTTPError):
            try:
                error_data = error.response.json()
            except ValueError:
                error_data = {
                    "status": error.response.status_code,
                    "message": error.response.content,
                }

            error_cls = HTTP_ERROR.get(error_data.get("status"), HTTPError)
            error = error_cls.parse(error_data)
        return error

    @staticmethod
    def _log_response(response, limit_size):
        # type: (requests.Response, int) -> None
        """
        Log the server's response based on its content type.

        :param response: The server's response to handle
        :param limit_size: Maximum size to not overflow when printing raw content
        of the response
        """

        headers = response.headers
        content_type = headers.get("content-type", "application/octet-stream")
        content = "<not yet handled, content-type={!r}>".format(content_type)

        if response.url.endswith("site/automation"):
            # This endpoint returns too many information and pollute logs.
            # Besides contents of this call are stored into the .operations attr.
            content = "<Automation details saved into the *operations* attr>"
        elif response.url.endswith("json/cmis"):
            # This endpoint returns too many information and pollute logs.
            # Besides contents of this call are stored into the .server_info attr.
            content = "<CMIS details saved into the *server_info* attr>"
        elif not response.content:
            # response.content is empty when *void_op* is True,
            # meaning we do not want to get back what we sent
            # or the operation does not return anything by default
            content = "<no content>"
        elif "application/octet-stream" in content_type:
            content = "<binary data>"
        elif "application/json" in content_type or content_type.startswith("text/"):
            content_size = int(headers.get("content-length", 0))
            content = "<too much data to display ({:,} bytes)>".format(content_size)
            if content_size <= limit_size:
                # Do not use response.text as it will load the chardet module and its
                # heavy encoding detection mecanism. The server will only return UTF-8.
                # See https://stackoverflow.com/a/24656254/1117028 and NXPY-100.
                content = response.content.decode("utf-8", errors="replace")

        logger.debug(
            "Response from {!r}: {!r} with headers {!r} and cookies {!r}".format(
                response.url, content, headers, response.cookies
            )
        )


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
        auth=None,  # type: Optional[Tuple[Text, Text]]
        host=DEFAULT_URL,  # type: Text
        app_name=DEFAULT_APP_NAME,  # type: Text
        version=__version__,  # type: Text
        client=NuxeoClient,  # type: Type[NuxeoClient]
        **kwargs  # type: Any
    ):
        # type: (...) -> None
        self.client = client(
            auth, host=host, app_name=app_name, version=version, **kwargs
        )
        self.operations = operations.API(self.client)
        self.directories = directories.API(self.client)
        self.groups = groups.API(self.client)
        self.tasks = tasks.API(self.client)
        self.uploads = uploads.API(self.client)
        self.users = users.API(self.client)
        self.workflows = workflows.API(self.client, self.tasks)
        self.documents = documents.API(self.client, self.operations, self.workflows)
