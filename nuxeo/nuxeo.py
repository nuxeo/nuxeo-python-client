# coding: utf-8
""" Nuxeo REST API Client. """
from __future__ import unicode_literals

import json
import logging
import socket
from urllib import urlencode

import base64
import requests
import tempfile
from collections import Sequence
from requests import HTTPError
from requests.cookies import RequestsCookieJar

from .batchupload import BatchUpload
from .blob import Blob
from .directory import Directory
from .exceptions import Unauthorized
from .groups import Groups
from .operation import Operation
from .repository import Repository
from .users import Users
from .workflow import Workflows

try:
    from typing import Any, Dict, List, Optional, Text, Union
except ImportError:
    pass

__all__ = ('Nuxeo',)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192  # Chunk size to download files

PARAM_TYPES = {  # Types allowed for operations parameters
    'blob': (unicode, Blob),
    'boolean': (bool,),
    'date': (unicode,),
    'document': (unicode,),
    'documents': (list,),
    'int': (int,),
    'integer': (int,),
    'long': (int, long),
    'map': (dict,),
    'object': (object,),
    'properties': (dict,),
    'resource': (unicode,),
    'serializable': (Sequence,),
    'string': (unicode,),
    'stringlist': (Sequence,),
    'validationmethod': (unicode,),
}  # type: Dict[unicode, Tuple[type, ...]])


def json_helper(o):
    # type: (Any) -> Dict[Text, Any]
    if hasattr(o, 'to_json'):
        return o.to_json()
    raise TypeError(repr(o) + 'is not JSON serializable (no to_json() found)')


class Nuxeo(object):
    """
    Client for the Nuxeo REST API.

    timeout is a short timeout to avoid having calls to fast JSON operations
    to block and freeze the application in case of network issues.

    blob_timeout is long (or infinite) timeout dedicated to long HTTP
    requests involving a blob transfer.

    :param base_url: Nuxeo server URL
    :param auth: Authentication parameter {'user': 'Administrator',
                                           'password': 'Administrator'}
    :param proxies: Proxy definition
    :param repository: Repository to use by default
    :param timeout: Client timeout
    :param blob_timeout: Binary download timeout
    :param cookie_jar: Cookie storage
    :param upload_tmp_dir: Tmp file to use for buffering
    :param api_path: Default API Path
    """

    __operations = None

    def __init__(
        self,
        base_url='http://localhost:8080/nuxeo',  # type: Text
        auth=None,                               # type: Dict[Text, Any]
        proxies=None,                            # type: Dict[Text, Any]
        repository='default',                    # type: Text
        timeout=20,                              # type: int
        blob_timeout=60,                         # type: int
        cookie_jar=None,                         # type: RequestsCookieJar
        upload_tmp_dir=None,                     # type: Text
        api_path='api/v1/',                      # type: Text
    ):
        # type: (...) -> None
        self._session = requests.session()
        self._session.proxies = proxies
        self._session.stream = True

        self.timeout = 20 if timeout is None or timeout < 0 else timeout
        socket.setdefaulttimeout(self.timeout)

        # Don't allow null timeout
        self.blob_timeout = (60 if blob_timeout is None or blob_timeout < 0
                             else blob_timeout)

        self.upload_tmp_dir = upload_tmp_dir or tempfile.gettempdir()

        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        if not api_path.endswith('/'):
            api_path += '/'

        self._repository = repository
        self.user_id = None

        self._auth = {}
        self._update_auth(auth=auth)
        self._headers = {'Cache-Control': 'no-cache'}

        if cookie_jar:
            self._session.cookies = cookie_jar

        self.automation_url = base_url + 'site/automation/'
        self.batch_upload_url = 'batch/upload'
        self.batch_execute_url = 'batch/execute'

        # New batch upload API
        self.new_upload_api_available = True
        self.rest_url = base_url + api_path
        self.batch_upload_path = 'upload'

    def batch_upload(self):
        # type: () -> BatchUpload
        """
        :return: Return a bucket to upload document to Nuxeo server
        """
        return BatchUpload(self)

    def check_params(self, command, params):
        # type: (Text, Dict[Text, Any]) -> None
        """
        Check given paramaters of the `command` operation.  It will also
        check for types whenever possible.

        :raises ValueError: When the `command` is not valid.
        :raises ValueError: On unexpected parameter.
        :raises ValueError: On missing required parameter.
        :raises TypeError: When a parameter has not the required type.
        """

        operation = self.operations.get(command)
        if not operation:
            raise ValueError('{!r} is not a registered operation'.format(command))

        parameters = {param['name']: param for param in operation['params']}

        for name, value in params.iteritems():
            # Check for unexpected parameters.  We use `dict.pop()` to
            # get and delete the parameter from the dict.
            try:
                type_needed = parameters.pop(name)['type']
            except KeyError:
                err = 'unexpected parameter {!r} for operation {!r}'
                raise ValueError(err.format(name, command))

            # Check types
            types_accepted = PARAM_TYPES.get(type_needed, tuple())
            if not isinstance(value, types_accepted):
                err = 'parameter {!r} should be of type {!r} (current {!r})'
                raise TypeError(err.format(
                    name, types_accepted, type(name).__name__))

        # Check for required parameters.  As of now, `parameters` may contain
        # unclaimed parameters and we just need to check for required ones.
        for name, parameter in parameters.iteritems():
            if parameter['required']:
                err = 'missing required parameter {!r} for operation {!r}'
                raise ValueError(err.format(name, command))

    def directory(self, name):
        # type: (Text) -> Directory
        """
        :return: An Operation object
        """
        return Directory(name, self)

    def drive_config(self):
        # type: () -> Dict[Text, Any]
        """
        Fetch the Drive JSON configuration from
        the $NUXEO_URL/api/v1/drive/configuration endpoint.
        """

        try:
            return self.send(self.rest_url + 'drive/configuration').json()
        except (HTTPError, ValueError, TypeError):
            logger.warning('Drive JSON configuration not found.')
        return {}

    def execute(
        self,
        command,             # type: Text
        url=None,            # type: Text
        op_input=None,       # type: Union[List[Text], Dict[Text, Any]]
        timeout=-1,          # type: int
        check_params=False,  # type: bool
        void_op=False,       # type: bool
        extra_headers=None,  # type: Dict[Text, Any]
        file_out=None,       # type: Text
        **params
    ):
        # type: (...) -> Union[Dict[Text, Any], Text]
        """
        Execute an Automation operation.

        :param command: Operation to execute
        :param url: Overrides the default url resolver
        :param op_input: Operation input
        :param timeout: Operation timeout
        :param check_params: Verify that the params are valid on the
                             client side
        :param void_op: If True, the response contains no data,
                        just the status
        :param extra_headers: Headers to add to the request
        :param file_out: Output result inside this file
        :param params: Any additional param to add to the request
        """

        if 'params' in params:
            params = params['params']
        if check_params:
            self.check_params(command, params)

        if url is None:
            url = self.automation_url + command
        headers = {
            'Content-Type': 'application/json+nxrequest',
            'Accept': 'application/json+nxentity, */*',
            'X-NXproperties': '*',
            # Keep compatibility with old header name
            'X-NXDocumentProperties': '*',
            'X-NXRepository': self._repository,
        }
        if void_op:
            headers['X-NXVoidOperation'] = 'true'
        if extra_headers:
            headers.update(extra_headers)

        json_struct = {'params': {}}
        for k, v in params.iteritems():
            if v is None:
                continue
            if k == 'properties':
                if isinstance(v, dict):
                    s = '\n'.join(['{}={}'.format(name, value) for name, value in v.iteritems()])
                else:
                    s = v
                json_struct['params'][k] = s.strip()
            else:
                json_struct['params'][k] = v

        if op_input:
            if isinstance(op_input, list):
                json_struct['input'] = "docs:" + ",".join(op_input)
            else:
                json_struct['input'] = op_input
        data = json.dumps(json_struct, default=json_helper)

        resp = self.send(url, method='POST', extra_headers=headers,
                         data=data, timeout=timeout)

        action = self.get_action()
        if action and action.progress is None:
            action.progress = 0

        if file_out:
            locker = self.lock_path(file_out)
            try:
                with open(file_out, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if action:
                            action.progress += CHUNK_SIZE
                        f.write(chunk)
                return file_out
            finally:
                self.unlock_path(file_out, locker)
        else:
            try:
                return resp.json()
            except ValueError:
                return resp.content

    def groups(self):
        # type: () -> Groups
        """
        :return: The Groups service
        """
        return Groups(self)

    def header(self, name, value):
        # type: (Text, Text) -> None
        """
        Define a header.

        :param name: -- Header name
        :param value: -- Header value
        """
        self._headers[name] = value

    def headers(self, extras=None):
        # type: (Optional[Dict[Text, Text]]) -> Dict[Text, Text]
        """
        Headers to include in every HTTP requests.

        Includes the authentication heads (token based or basic auth if no
        token).

        Also include an application name header to make it possible for the
        server to compute access statistics for various client types (e.g.
        browser vs devices).

        You can set additional headers with the extras argument.

        :param extras: -- a dictionary or object of additional headers to set
        """
        headers = self._headers.copy()

        if extras:
            headers.update(extras)
        if self._auth:
            headers.update(self._auth)

        return headers

    def lock_path(self, file_out):
        # type: (Text) -> None
        pass

    def login(self):
        # type: () -> User
        """
        Try to login and return the user.

        :return: Current user
        """
        self.execute('login')
        return self.users().fetch(self.user_id)

    def operation(self, name):
        # type: (Text) -> Operation
        """
        https://doc.nuxeo.com/display/NXDOC/Automation

        :return: An Operation object to perform on Automation
        """
        return Operation(name, self)

    @property
    def operations(self):
        # type: () -> Dict[Text, Any]
        """
        A dict of all operations and their parameters.
        Fetched on demand as it is a heavy work for the server and the network.

        :rtype: dict
        """

        if not self.__operations:
            self.__operations = self._fetch_api()
        return self.__operations

    def repository(self, name='default', schemas=None):
        # type: (Text, Optional[Text]) -> Repository
        """
        :return: A repository object
        """
        return Repository(name, self, schemas=schemas or [])

    def request(
        self,
        relative_url,                       # type: Text
        body=None,                          # type: Optional[Union[Text, Dict[Text, Any], bytes]]
        adapter=None,                       # type: Optional[Text]
        timeout=-1,                         # type: int
        method='GET',                       # type: Text
        content_type='application/json',    # type: Text
        extra_headers=None,                 # type: Optional[Dict[Text, Text]]
        raw_body=False,                     # type: bool
        query_params=None,                  # type: Optional[Dict[Text, Any]]
    ):
        # type: (...) -> Union[Dict[Text, Any], Text, bytes]
        """
        Execute a REST API call.

        :param relative_url: URL to call relative to the rest_url provide in
                             constructor.
        :param body: Body of the request
        :param adapter: If specified will add the @adapter at the end of
                        the URL.
        :param timeout: Timeout
        :param method: HTTP method to use
        :param content_type: For the request
        :param extra_headers: Additional headers to send
        :param raw_body: Avoid any processing on the body, by default body
                         are serialized to json
        :param query_params: Dict of the query parameter to add to the
                             request ?param1=value1&param2=value2
        """

        url = self.rest_url + relative_url
        if adapter:
            url += '/@' + adapter

        if body and not isinstance(body, bytes) and not raw_body:
            body = json.dumps(body, default=json_helper)

        headers = {
            'Content-Type': content_type,
            'Accept': 'application/json+nxentity, */*',
        }
        if extra_headers:
            headers.update(extra_headers)

        resp = self.send(url, method=method, params=query_params,
                         extra_headers=headers, data=body, timeout=timeout)
        try:
            return resp.json()
        except ValueError:
            return resp.content

    def request_authentication_token(
        self,
        application_name,       # type: Text
        device_id,              # type: Text
        device_description,     # type: Text
        permission,             # type: Text
        revoke=False,           # type: bool
    ):
        # type: (...) -> Text
        """
        Request and return a new token for the user.

        Token requires to have an application name and device id and permission
        the description is optional.  Once the token received you can use it
        for future login
        """

        parameters = {
            'deviceId': device_id,
            'applicationName': application_name,
            'permission': permission,
            'revoke': str(revoke).lower(),
        }
        if device_description:
            parameters['deviceDescription'] = device_description
        url = self.base_url + 'authentication/token?'
        url += urlencode(parameters)

        token = self.send(url).text

        # Use the (potentially re-newed) token from now on
        if not revoke:
            self._update_auth(token=token)
        return token

    def send(
            self,
            url,                    # type: Text
            method='GET',           # type: Text
            data=None,              # type: Optional[Union[Text, Dict[Text, Any], bytes]]
            params=None,            # type: Optional[Dict[Text, Any]]
            extra_headers=None,     # type: Optional[Dict[Text, Text]]
            timeout=None            # type: Optional[int]
    ):
        # type: (...) -> requests.Response
        """
        Perform a request to the server.

        This method acts as a wrapper for the request to handle the errors
        and the logging. All other methods use this one to send their requests.

        :param url: URL for the HTTP request
        :param method: Method of the HTTP request
        :param data: Body of the request (text or bytes)
        :param params: Parameters to encode in the URL
        :param extra_headers: Headers to add to the common ones
        :param timeout: Timeout for the request
        :return: The HTTP request response (Response object)
        """
        if method not in ('GET', 'HEAD', 'POST', 'PUT',
                          'DELETE', 'CONNECT', 'OPTIONS', 'TRACE'):
            raise ValueError('method parameter is not a valid HTTP method.')

        timeout = self.timeout if not timeout or timeout == -1 else timeout
        headers = self.headers(extra_headers)

        logger.debug('Calling {!r} with headers={!r}, params={!r} and cookies={!r}'.format(
            url, headers, params, self._session.cookies))

        try:
            resp = self._session.request(url=url, method=method, headers=headers,
                                         params=params, data=data, timeout=timeout)
            resp.raise_for_status()
        except Exception as e:
            if isinstance(e, HTTPError) and e.response.status_code in (401, 403):
                e = Unauthorized(self.user_id, e)
            self._log_details(e)
            raise e

        if int(resp.headers.get('content-length', CHUNK_SIZE + 1)) <= CHUNK_SIZE:
            content = resp.content
        else:
            content = '<Too much data to display>'

        logger.debug('Response from {!r}: {!r} with cookies {!r}'.format(
            url, content, self._session.cookies))

        return resp

    def server_reachable(self):
        # type: () -> bool
        """
        Simple call to the server status page to check if it is reachable.
        """

        try:
            resp = self.send(self.base_url + 'runningstatus')
            return resp.ok
        except HTTPError:
            pass
        return False

    def unlock_path(self, file_out, locker):
        # type: (Text, None) -> None
        return None

    def users(self):
        # type: () -> Users
        """
        :return: The Users service
        """
        return Users(self)

    def workflows(self):
        # type: () -> Workflows
        """
        :return: The Workflows service
        """
        return Workflows(self)

    def create_action(self, type, path, name):
        # type: (Text, Text, Text) -> Dict[Text, Any]
        return {}

    def end_action(self):
        # type: () -> None
        pass

    def _fetch_api(self):
        # type: () -> Dict[Text, Any]
        """ Used to populate :attr:`operations`, do not call directly. """

        resp = self.send(self.automation_url)
        resp = resp.json()

        operations = {}
        for operation in resp['operations']:
            operations[operation['id']] = operation
            for alias in operation.get('aliases', []):
                operations[alias] = operation
        return operations

    def get_action(self):
        # type: () -> None
        return None

    def _log_details(self, e):
        # type: (Exception) -> None
        if isinstance(e, HTTPError):
            logger.exception(u'Remote exception: {}'.format(
                e.message.decode('utf-8')))
            try:
                exc = e.response.json()
                message = exc.get('message')
                stack = exc.get('stacktrace')
                if message:
                    logger.error('Remote exception message: {!s}'.format(message))
                if stack:
                    logger.error('Remote exception stack: {!s}'.format(stack))
                else:
                    logger.error('Remote exception details: {!s}'.format(exc))
            except ValueError:
                # Error messages from the server should always be JSON-formatted,
                # but sometimes they're not
                logger.error('Response is not JSON')
        else:
            # The error was not sent from the server
            logger.exception('Local exception')

    def _update_auth(self, auth=None, password=None, token=None):
        # type: (Optional[Dict[Text, Any]], Optional[Text], Optional[Text]) -> None
        """
        When username retrieved from database, check for unicode and convert
        to string.
        Note: base64Encoding for unicode type will fail, hence converting
        to string.
        """

        if auth:
            self.user_id = auth.get('username', None)
            token = auth.get('token', token)
            password = auth.get('password', password)

        # Select the most appropriate auth headers based on credentials
        if token:
            self._auth = {'X-Authentication-Token': token}
        elif password:
            self._auth = {'Authorization': 'Basic {}'.format(
                base64.b64encode('{}:{}'.format(
                    self.user_id, password).encode('utf-8')).strip())}
        else:
            raise ValueError('Either password or token must be provided')
