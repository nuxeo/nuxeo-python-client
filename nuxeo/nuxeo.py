# coding: utf-8
""" Nuxeo REST API Client. """
from __future__ import unicode_literals

import base64
import json
import logging
import socket
import tempfile
from collections import Sequence
from urllib import urlencode

import requests
from requests import HTTPError

from .batchupload import BatchUpload
from .blob import Blob
from .directory import Directory
from .exceptions import Unauthorized
from .groups import Groups
from .operation import Operation
from .repository import Repository
from .users import Users
from .workflow import Workflows

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


def force_decode(string, codecs=('utf-8', 'cp1252')):
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    for codec in codecs:
        try:
            return string.decode(codec)
        except UnicodeError:
            pass
    return None


def json_helper(o):
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
    :param check_suspended: Method to call while doing network call so you
                           can interrupt the download thread
    :param api_path: Default API Path
    """

    __operations = None

    def __init__(
        self,
        base_url='http://localhost:8080/nuxeo',
        auth=None,
        proxies=None,
        repository='default',
        timeout=20,
        blob_timeout=60,
        cookie_jar=None,
        upload_tmp_dir=None,
        check_suspended=None,
        api_path='api/v1/',
    ):
        self._session = requests.session()
        self._session.proxies = proxies
        self._session.stream = True

        # Function to check during long-running processing like upload /
        # download if the synchronization thread needs to be suspended
        self.check_suspended = check_suspended

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
        """
        :return: Return a bucket to upload document to Nuxeo server
        """
        return BatchUpload(self)

    def check_params(self, command, params):
        # type: (unicode, Dict[unicode, Tuple[type, ...]]) -> None
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
        """
        :return: An Operation object
        """
        return Directory(name, self)

    def drive_config(self):
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
        command,
        url=None,
        op_input=None,
        timeout=-1,
        check_params=False,
        void_op=False,
        extra_headers=None,
        file_out=None,
        **params
    ):
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
            locker = self.unlock_path(file_out)
            try:
                with open(file_out, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                        if action:
                            action.progress += CHUNK_SIZE
                        f.write(chunk)
                return file_out
            finally:
                self.lock_path(file_out, locker)
        else:
            try:
                return resp.json()
            except ValueError:
                return resp.content

    def groups(self):
        """
        :return: The Groups service
        """
        return Groups(self)

    def header(self, name, value):
        """
        Define a header.

        :param name: -- Header name
        :param value: -- Header value
        """
        self._headers[name] = value

    def headers(self, extras=None):
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

    def lock_path(self, file_out, locker):
        pass

    def login(self):
        """
        Try to login and return the user.

        :return: Current user
        """
        self.execute('login')
        return self.users().fetch(self.user_id)

    def operation(self, name):
        """
        https://doc.nuxeo.com/display/NXDOC/Automation

        :return: An Operation object to perform on Automation
        """
        return Operation(name, self)

    @property
    def operations(self):
        """
        A dict of all operations and their parameters.
        Fetched on demand as it is a heavy work for the server and the network.

        :rtype: dict
        """

        if not self.__operations:
            self.__operations = self._fetch_api()
        return self.__operations

    def repository(self, name='default', schemas=None):
        """
        :return: A repository object
        """
        return Repository(name, self, schemas=schemas or [])

    def request(
        self,
        relative_url,
        body=None,
        adapter=None,
        timeout=-1,
        method='GET',
        content_type='application/json',
        extra_headers=None,
        raw_body=False,
        query_params=None,
    ):
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
        application_name,
        device_id,
        device_description,
        permission,
        revoke=False,
    ):
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

    def send(self, url, method='GET', data=None, params=None, extra_headers=None, timeout=None):
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

        logger.debug('Calling {!r} with headers {!r} and cookies {!r}'.format(
            url, headers, self._get_cookies()))

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
            url, content, self._get_cookies()))

        return resp

    def server_reachable(self):
        """
        Simple call to the server status page to check if it is reachable.
        """

        try:
            resp = self.send(self.base_url + 'runningstatus')
            return resp.ok
        except HTTPError:
            pass
        return False

    def unlock_path(self, file_out):
        return None

    def users(self):
        """
        :return: The Users service
        """
        return Users(self)

    def workflows(self):
        """
        :return: The Workflows service
        """
        return Workflows(self)

    def create_action(self, type, path, name):
        return {}

    def end_action(self):
        pass

    def _fetch_api(self):
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
        return None

    def _get_cookies(self):
        return list(self._session.cookies) or []

    def _log_details(self, e):
        if isinstance(e, HTTPError):
            logger.exception(u'Remote exception: {}'.format(
                e.message.decode('utf-8')))
            try:
                exc = e.response.json()
                message = exc.get('message')
                stack = exc.get('stacktrace')
                error = exc.get('error')
                if message:
                    logger.error('Remote exception message: {!s}'.format(message))
                if stack:
                    logger.error('Remote exception stack: {!s}'.format(stack))
                else:
                    logger.error('Remote exception details: {!s}'.format(exc))
                return exc.get('status'), exc.get('code'), message, error
            except ValueError:
                # Error messages from the server should always be JSON-formatted,
                # but sometimes they're not
                logger.error('Response is not JSON')
        else:
            # The error was not sent from the server
            logger.exception('Local exception')

    def _update_auth(self, auth=None, password=None, token=None):
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
