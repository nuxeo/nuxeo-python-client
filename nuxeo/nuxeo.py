# coding: utf-8
""" Nuxeo REST API Client. """
from __future__ import unicode_literals

import base64
import json
import socket
import tempfile
import urllib2
from collections import Sequence
from urllib import urlencode

from .batchupload import BatchUpload
from .blob import Blob
from .directory import Directory
from .groups import Groups
from .operation import Operation
from .repository import Repository
from .users import Users
from .workflow import Workflows

__all__ = ('Nuxeo',)

PARAM_TYPES = {
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


class InvalidBatchException(Exception):
    pass


class Nuxeo(object):
    """
    Client for the Nuxeo REST API.

    timeout is a short timeout to avoid having calls to fast JSON operations
    to block and freeze the application in case of network issues.

    blob_timeout is long (or infinite) timeout dedicated to long HTTP
    requests involving a blob transfer.

    TODO: Switch to Requests to handle proxy

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
        self._headers = {}

        # Function to check during long-running processing like upload /
        # download if the synchronization thread needs to be suspended
        self.check_suspended = check_suspended

        self.timeout = 20 if timeout is None or timeout < 0 else timeout
        socket.setdefaulttimeout(self.timeout)

        # Don't allow null timeout
        self.blob_timeout = (60 if blob_timeout is None or blob_timeout < 0
                             else blob_timeout)

        self.upload_tmp_dir = (upload_tmp_dir if upload_tmp_dir is not None
                               else tempfile.gettempdir())

        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        if not api_path.endswith('/'):
            api_path += '/'

        self._repository = repository
        self.user_id = None
        self._auth = ['', '']
        self._update_auth(auth=auth)
        self.cookie_jar = cookie_jar
        cookie_processor = urllib2.HTTPCookieProcessor(
            cookiejar=cookie_jar)

        # Build URL openers
        self.streaming_opener = urllib2.build_opener(cookie_processor)
        self.opener = self.streaming_opener

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

    def debug(self, *args, **kwargs):
        pass

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

        url = self.rest_url + 'drive/configuration'
        headers = self._get_common_headers()
        self.trace('Fetching the Drive configuration at %r with headers=%r',
                   url, headers)
        req = Request(url, headers=headers)
        try:
            ret = self.opener.open(req, timeout=self.timeout)
            return json.loads(ret.read())
        except (urllib2.URLError, ValueError):
            pass
        return {}

    def error(self, *args, **kwargs):
        pass

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
        :param void_op: If operation is a void operation
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
        }
        if void_op:
            headers.update({'X-NXVoidOperation': 'true'})
        headers.update({'X-NXRepository': self._repository})
        if extra_headers:
            headers.update(extra_headers)
        headers.update(self._get_common_headers())

        json_struct = {'params': {}}
        for k, v in params.iteritems():
            if v is None:
                continue
            if k == 'properties':
                if isinstance(v, dict):
                    s = ''
                    for propname, propvalue in v.iteritems():
                        s += '%s=%s\n' % (propname, propvalue)
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

        req = urllib2.Request(url, data, headers)
        timeout = self.timeout if timeout == -1 else timeout

        try:
            resp = self.opener.open(req, timeout=timeout)
        except Exception as e:
            log_details = self._log_details(e)
            if isinstance(log_details, tuple):
                _, _, _, error = log_details
                if error and error.startswith("Unable to find batch"):
                    raise InvalidBatchException()
            raise e

        action = self._get_action()
        if action and action.progress is None:
            action.progress = 0

        if file_out is not None:
            locker = self.unlock_path(file_out)
            try:
                with open(file_out, 'wb') as f:
                    while 'downloading':
                        # Check if synchronization thread was suspended
                        if self.check_suspended is not None:
                            self.check_suspended('File download: %s'
                                                 % file_out)
                        buffer_ = resp.read(self.get_download_buffer())
                        if buffer_ == '':
                            break
                        if action:
                            action.progress += self.get_download_buffer()
                        f.write(buffer_)
                return None, file_out
            finally:
                self.lock_path(file_out, locker)
        else:
            return self._read_response(resp, url)

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
        Return the headers that will be sent to the server
        You can set additional headers with extras argument.

        :param extras: -- a dictionary or object of additional headers to set
        """
        headers = self._get_common_headers()
        if extras:
            self._headers.update(extras)
        headers.update(self._headers)
        return headers

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
        if adapter is not None:
            url += '/@' + adapter

        if query_params:
            url += '?' + urlencode(query_params)

        if body is not None and not isinstance(body, str) and not raw_body:
            body = json.dumps(body, default=json_helper)

        headers = {
            'Content-Type': content_type,
            'Accept': 'application/json+nxentity, */*',
        }
        headers.update(self._get_common_headers())
        if extra_headers is not None:
            headers.update(extra_headers)
        cookies = self._get_cookies()
        self.trace('Calling REST API %s with headers %r and cookies %r',
                   url, headers, cookies)
        req = Request(url, headers=headers, method=method, data=body)
        timeout = self.timeout if timeout == -1 else timeout
        try:
            resp = self.opener.open(req, timeout=timeout)
        except Exception as e:
            self._log_details(e)
            raise e

        return self._read_response(resp, url)

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

        err = ('Failed to connect to Nuxeo server {} with user {}'
               ' to acquire a token').format(self.base_url, self.user_id)
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

        headers = self._get_common_headers()
        cookies = self._get_cookies()
        self.trace('Calling %s with headers %r and cookies %r',
                   url, headers, cookies)
        req = urllib2.Request(url, headers=headers)
        try:
            token = self.opener.open(req, timeout=self.timeout).read()
        except urllib2.HTTPError as e:
            if e.code == 401 or e.code == 403:
                raise Unauthorized(self.base_url, self.user_id, e.code)
            elif e.code == 404:
                # Token based auth is not supported by this server
                return None
            else:
                e.msg = err + ': HTTP error %d' % e.code
                raise e
        except Exception as e:
            if hasattr(e, 'msg'):
                e.msg = err + ': ' + e.msg
            raise
        cookies = self._get_cookies()
        self.trace('Got token %r with cookies %r', token, cookies)
        # Use the (potentially re-newed) token from now on
        if not revoke:
            self._update_auth(token=token)
        return token

    def server_reachable(self):
        """
        Simple call to the server status page to check if it is reachable.
        """

        url = self.base_url + 'runningstatus'
        headers = self._get_common_headers()
        self.trace('Checking server availability at %r with headers=%r',
                   url, headers)
        req = urllib2.Request(url, headers=headers)
        try:
            ret = self.opener.open(req, timeout=self.timeout)
        except urllib2.URLError:
            pass
        else:
            if ret.code == 200:
                return True
        return False

    def trace(self, *args, **kwargs):
        pass

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
            raise ValueError('%r is not a registered operation' % command)

        parameters = {param['name']: param for param in operation['params']}

        for name, value in params.iteritems():
            # Check for unexpected paramaters.  We use `dict.pop()` to
            # get and delete the parameter from the dict.
            try:
                type_needed = parameters.pop(name)['type']
            except KeyError:
                err = 'unexpected parameter %r for operation %r'
                raise ValueError(err, name, command)

            # Check types
            types_accepted = PARAM_TYPES.get(type_needed, tuple())
            if not isinstance(value, types_accepted):
                err = 'parameter {!r} should be of type {!r} (current %s)'
                raise TypeError(err.format(
                    name, types_accepted, type(name).__name__))

        # Check for required parameters.  As of now, `parameters` may contain
        # unclaimed parameters and we just need to check for required ones.
        for name, parameter in parameters.iteritems():
            if parameter['required']:
                err = 'missing required parameter {!r} for operation {!r}'
                raise ValueError(err.format(name, command))

    def _create_action(self, type, path, name):
        return {}

    def _end_action(self):
        pass

    def _fetch_api(self):
        """ Used to populate :attr:`operations`, do not call directly. """

        err = 'Failed to connect to Nuxeo server {}'.format(self.base_url)
        url = self.automation_url
        headers = self._get_common_headers()
        cookies = self._get_cookies()
        self.trace('Calling %s with headers %r and cookies %r',
                   url, headers, cookies)
        req = urllib2.Request(url, headers=headers)
        try:
            response = json.loads(
                self.opener.open(req, timeout=self.timeout).read())
        except urllib2.HTTPError as e:
            if e.code in (401, 403):
                raise Unauthorized(self.base_url, self.user_id, e.code)

            msg = err + '\nHTTP error %d' % e.code
            if hasattr(e, 'msg'):
                msg = msg + ': ' + e.msg
            e.msg = msg
            raise e
        except urllib2.URLError as e:
            msg = err
            if hasattr(e, 'message') and e.message:
                e_msg = force_decode(': ' + e.message)
                if e_msg is not None:
                    msg += e_msg
            elif hasattr(e, 'reason') and e.reason:
                if (hasattr(e.reason, 'message')
                        and e.reason.message):
                    e_msg = force_decode(': ' + e.reason.message)
                    if e_msg is not None:
                        msg += e_msg
                elif (hasattr(e.reason, 'strerror')
                        and e.reason.strerror):
                    e_msg = force_decode(': ' + e.reason.strerror)
                    if e_msg is not None:
                        msg += e_msg
            msg += ('\nPlease check your Internet connection,'
                    + ' make sure the Nuxeo server URL is valid'
                    + '" and check your proxy settings.')
            e.msg = msg
            raise e
        except Exception as e:
            msg = err
            if hasattr(e, 'msg'):
                msg += ': ' + e.msg
            e.msg = msg
            raise e

        operations = {}
        for operation in response['operations']:
            operations[operation['id']] = operation
            for alias in operation.get('aliases', []):
                operations[alias] = operation
        return operations

    def _get_action(self):
        return None

    def _get_common_headers(self):
        """
        Headers to include in every HTTP requests.

        Includes the authentication heads (token based or basic auth if no
        token).

        Also include an application name header to make it possible for the
        server to compute access statistics for various client types (e.g.
        browser vs devices).
        """

        headers = {
            'Cache-Control': 'no-cache',
        }
        if self._auth is not None:
            headers.update([self._auth])
        headers.update(self._headers)
        return headers

    def _get_cookies(self):
        return list(self.cookie_jar) if self.cookie_jar is not None else []

    def _log_details(self, e):
        if hasattr(e, 'fp'):
            detail = e.fp.read().decode('utf-8')
            try:
                exc = json.loads(detail)
                message = exc.get('message')
                stack = exc.get('stack')
                error = exc.get('error')
                if message:
                    self.debug('Remote exception message: %s', message)
                if stack:
                    self.debug('Remote exception stack: %r',
                               exc['stack'], exc_info=True)
                else:
                    self.debug('Remote exception details: %r', detail)
                return exc.get('status'), exc.get('code'), message, error
            except ValueError:
                # Error message should always be a JSON message,
                # but sometimes it's not
                if '<html>' in detail:
                    message = e
                else:
                    message = detail
                self.error(message)
                if isinstance(e, urllib2.HTTPError):
                    return e.code, None, message, None
        return None

    def _read_response(self, response, url):
        info = response.info()
        s = response.read()
        content_type = info.get('content-type', '')
        cookies = self._get_cookies()
        if content_type.startswith('application/json'):
            self.trace('Response for %r with cookies %r: %r',
                       url, cookies, s)
            return json.loads(s) if s else None
        else:
            self.trace('Response for %r with cookies %r has content-type %r',
                       url, cookies, content_type)
            return s

    def _update_auth(self, auth=None, password=None, token=None):
        """
        When username retrieved from database, check for unicode and convert
        to string.
        Note: base64Encoding for unicode type will fail, hence converting
        to string.
        """

        if auth is not None:
            if 'username' in auth:
                self.user_id = auth['username']
            if 'token' in auth:
                token = auth['token']
            if 'password' in auth:
                password = auth['password']

        if self.user_id and isinstance(self.user_id, unicode):
            self.user_id = unicode(self.user_id).encode('utf-8')

        # Select the most appropriate auth headers based on credentials
        if token is not None:
            self._auth = ('X-Authentication-Token', token)
        elif password is not None:
            basic_auth = 'Basic %s' % base64.b64encode(
                    self.user_id + ":" + password).strip()
            self._auth = 'Authorization', basic_auth
        else:
            raise ValueError('Either password or token must be provided')


class Request(urllib2.Request):
    """ Need to override urllib2 request to add the HTTP method. """

    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', 'GET')
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


class Unauthorized(Exception):

    def __init__(self, server_url, user_id, code=403):
        self.server_url = server_url
        self.user_id = user_id
        self.code = code

    def __str__(self):
        return ('%r is not authorized to access %r with '
                ' the provided credentials' % (self.user_id, self.server_url))
