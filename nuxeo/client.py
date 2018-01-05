# coding: utf-8
from __future__ import unicode_literals

import atexit
import json
import logging

import requests

from . import __version__, directories, documents, groups, operations, tasks, \
    uploads, users, workflows
from .auth import TokenAuth
from .compat import text, urlencode
from .exceptions import HTTPError, Unauthorized
from .utils import json_helper

try:
    from typing import Any, Dict, Text, Tuple, Type, Optional
except ImportError:
    pass

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192  # Chunk size to download files
DEFAULT_URL = 'http://localhost:8080/nuxeo/'
DEFAULT_API_PATH = 'api/v1'
DEFAULT_APP_NAME = 'Python client'


class NuxeoClient(object):
    """ The HTTP client used by Nuxeo """

    def __init__(
        self,
        auth=None,                  # type: Optional[Tuple(Text, Text)]
        host=DEFAULT_URL,           # type: Text
        api_path=DEFAULT_API_PATH,  # type: Text
        app_name=DEFAULT_APP_NAME,  # type: Text
        chunk_size=CHUNK_SIZE,      # type: int
        **kwargs                    # type: **Any
    ):
        # type: (...) -> None

        self.auth = auth
        self.host = host
        self.api_path = api_path
        self.headers = {
            'X-Application-Name': app_name,
            'X-Client-Version': __version__,
            'Accept': 'application/json+nxentity, */*'
        }
        self.chunk_size = chunk_size
        self.schemas = kwargs.get('schemas', '*')
        self.repository = kwargs.get('repository', 'default')
        self.client_kwargs = kwargs
        self._session = requests.session()
        self._session.stream = True
        atexit.register(self.on_exit)

        # Ensure the host is well formated
        if not self.host.endswith('/'):
            self.host += '/'

    def on_exit(self):
        self._session.close()

    def set(self, repository=None, schemas=None):
        # type: (Optional[Text], Optional[Text]) -> NuxeoClient
        """
        Set the repository and/or the schemas for the requests.

        :return: the client instance after adding the settings
        """
        if repository:
            self.repository = repository

        if schemas:
            if isinstance(schemas, list):
                schemas = ','.join(schemas)
            self.schemas = schemas

        return self

    def request(
        self,
        method,        # type: Text
        path,          # type: Text
        headers=None,  # type: Optional[Dict[Text, Text]]
        data=None,     # type: Optional[Any]
        raw=False,     # type: bool
        **kwargs       # type: **Any
    ):
        # type: (...) -> requests.Response
        """
        Send a request to the Nuxeo server.

        :param method: the HTTP method
        :param path: the path to append to the host host
        :param headers: the headers for the HTTP request
        :param data: data to put in the body
        :param raw: if True, don't parse the data to JSON
        :param kwargs: other parameters accepted by requests
        :return: the HTTP response
        """
        if method not in ('GET', 'HEAD', 'POST', 'PUT',
                          'DELETE', 'CONNECT', 'OPTIONS', 'TRACE'):
            raise ValueError('method parameter is not a valid HTTP method.')

        # Construct the full URL without double slashes
        url = self.host + path.lstrip('/')
        if 'adapter' in kwargs:
            url = '{}/@{}'.format(url, kwargs.pop('adapter'))

        kwargs.update(self.client_kwargs)

        headers = headers or {}
        headers.update({
            'Content-Type': kwargs.get('content_type', 'application/json'),
            'X-NXDocumentProperties': self.schemas,
            'X-NXRepository': self.repository
        })
        headers.update(self.headers)

        if data and not isinstance(data, bytes) and not raw:
            data = json.dumps(data, default=json_helper)

        default = kwargs.pop('default', object)

        logger.debug(
            'Calling {!r} with headers={!r}, params={!r} and cookies={!r}'.format(
                url, headers, kwargs.get('params', {}), self._session.cookies))

        try:
            resp = self._session.request(
                method, url, headers=headers, auth=self.auth, data=data, **kwargs)
            resp.raise_for_status()
        except Exception as exc:
            if default is object:
                raise self._handle_error(exc)
            resp = default
        else:
            content_size = resp.headers.get('content-length', self.chunk_size)
            if int(content_size) <= self.chunk_size:
                content = resp.content
            else:
                content = '<Too much data to display>'
            logger.debug('Response from {!r}: {!r} with cookies {!r}'.format(
                url, content, self._session.cookies))

        return resp

    def request_auth_token(
        self,
        device_id,                  # type: Text
        permission,                 # type: Text
        app_name=DEFAULT_APP_NAME,  # type: Text
        device=None,                # type: Optional[Text]
        revoke=False                # type: bool
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
            'deviceId': device_id,
            'applicationName': app_name,
            'permission': permission,
            'revoke': text(revoke).lower(),
        }
        if device:
            parameters['deviceDescription'] = device

        path = 'authentication/token?' + urlencode(parameters)
        token = self.request('GET', path).text

        # Use the (potentially re-newed) token from now on
        if not revoke:
            self.auth = TokenAuth(token)
        return token

    def is_reachable(self):
        response = self.request('GET', 'runningstatus', default=False)
        if isinstance(response, requests.Response):
            return response.ok
        else:
            return response

    @staticmethod
    def _handle_error(error):
        # type: (Exception) -> Exception
        """
        Log error and handle raise.

        :param error: the error to handle
        """
        if isinstance(error, requests.HTTPError):
            try:
                error_data = error.response.json()
            except ValueError:
                error_data = {'status': error.response.status_code,
                              'message': error.response.content}

            error_class = Unauthorized if error_data.get('status') in (401, 403) else HTTPError
            error = error_class.parse(error_data)
            logger.exception('Remote exception: {}'.format(error))
        else:
            logger.exception(error)
        return error


class Nuxeo(object):
    def __init__(
        self,
        auth=None,                  # type: Optional[Tuple(Text, Text)]
        host=DEFAULT_URL,           # type: Text
        app_name=DEFAULT_APP_NAME,  # type: Text
        client=NuxeoClient,         # type: Type[NuxeoClient]
        **kwargs                    # type: **Any
    ):
        # type: (...) -> None
        """
        Instantiate the client and all the API Endpoints.

        :param auth: the authenticator
        :param host: the host URL
        :param app_name: the name of the application using the client
        :param client: the client class
        :param kwargs: any other argument to forward to every requests calls
        """

        if requests.__version__ < '2.12.2':
            from warnings import warn
            warn('Requests >= 2.12.2 required for auth unicode support.')

        self.client = client(auth, host=host, app_name=app_name, **kwargs)
        self.operations = operations.API(self.client)
        self.directories = directories.API(self.client)
        self.documents = documents.API(self.client, self.operations)
        self.groups = groups.API(self.client)
        self.tasks = tasks.API(self.client)
        self.uploads = uploads.API(self.client)
        self.users = users.API(self.client)
        self.workflows = workflows.API(self.client)
