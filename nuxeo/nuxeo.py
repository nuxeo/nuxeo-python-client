# coding: utf-8
""" Nuxeo REST API Client. """

import base64
import json
import socket
import tempfile
from urllib import urlencode

import urllib2
from poster.streaminghttp import get_handlers
from urllib2 import ProxyHandler
from urlparse import urlparse

from .batchupload import BatchUpload
from .directory import Directory
from .groups import Groups
from .operation import Operation
from .repository import Repository
from .users import Users
from .workflow import Workflows

__all__ = ['Nuxeo']


def json_helper(o):
    if (hasattr(o, 'to_json')):
        res = o.to_json()
        return res
    raise TypeError(repr(o) + "is not JSON serializable (no to_json found)")

def force_decode(string, codecs=['utf-8', 'cp1252']):
    if isinstance(string, unicode):
        string = string.encode('utf-8')
    for codec in codecs:
        try:
            return string.decode(codec)
        except:
            pass
    return None


class InvalidBatchException(Exception):
    pass


def get_proxies_for_handler(proxy_settings):
    """Return a pair containing proxy string and exceptions list"""
    if proxy_settings.config == 'None':
        # No proxy, return an empty dictionary to disable
        # default proxy detection
        return {}, None
    elif proxy_settings.config == 'System':
        # System proxy, return None to use default proxy detection
        return None, None
    else:
        # Manual proxy settings, build proxy string and exceptions list
        if proxy_settings.authenticated:
            proxy_string = ("%s:%s@%s:%s") % (
                                proxy_settings.username,
                                proxy_settings.password,
                                proxy_settings.server,
                                proxy_settings.port)
        else:
            proxy_string = ("%s:%s") % (
                                proxy_settings.server,
                                proxy_settings.port)
        if proxy_settings.proxy_type is None:
            proxies = {'http': proxy_string, 'https': proxy_string}
        else:
            proxies = {proxy_settings.proxy_type: ("%s://%s" % (proxy_settings.proxy_type, proxy_string))}
        if proxy_settings.exceptions and proxy_settings.exceptions.strip():
            proxy_exceptions = [e.strip() for e in
                                proxy_settings.exceptions.split(',')]
        else:
            proxy_exceptions = None
        return proxies, proxy_exceptions


def get_proxy_config(proxies):
    if proxies is None:
        return 'System'
    elif proxies == {}:
        return 'None'
    else:
        return 'Manual'


def get_proxy_handler(proxies, proxy_exceptions=None, url=None):
    if proxies is None:
        # No proxies specified, use default proxy detection
        return urllib2.ProxyHandler()
    else:
        # Use specified proxies (can be empty to disable default detection)
        if proxies:
            if proxy_exceptions is not None and url is not None:
                hostname = urlparse(url).hostname
                for exception in proxy_exceptions:
                    if exception == hostname:
                        # Server URL is in proxy exceptions,
                        # don't use any proxy
                        proxies = {}
        return urllib2.ProxyHandler(proxies)


def get_opener_proxies(opener):
    for handler in opener.handlers:
        if isinstance(handler, ProxyHandler):
            return handler.proxies
    return None


class Unauthorized(Exception):

    def __init__(self, server_url, user_id, code=403):
        self.server_url = server_url
        self.user_id = user_id
        self.code = code

    def __str__(self):
        return ("'%s' is not authorized to access '%s' with"
                " the provided credentials" % (self.user_id, self.server_url))


class Request(urllib2.Request):
    """Need to override urllib2 request to add the HTTP method
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', 'GET')
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


class Nuxeo(object):
    """Client for the Nuxeo REST API

    timeout is a short timeout to avoid having calls to fast JSON operations
    to block and freeze the application in case of network issues.

    blob_timeout is long (or infinite) timeout dedicated to long HTTP
    requests involving a blob transfer.

    Supports HTTP proxies.
    If proxies is given, it must be a dictionary mapping protocol names to
    URLs of proxies.
    If proxies is None, uses default proxy detection:
    read the list of proxies from the environment variables <PROTOCOL>_PROXY;
    if no proxy environment variables are set, then in a Windows environment
    proxy settings are obtained from the registry's Internet Settings section,
    and in a Mac OS X environment proxy information is retrieved from the
    OS X System Configuration Framework.
    To disable autodetected proxy pass an empty dictionary.
    """
    # TODO: handle system proxy detection under Linux,
    # see https://jira.nuxeo.com/browse/NXP-12068
    ##
    # @param base_url   Nuxeo server URL
    # @param auth   Authentication parameter {'user': 'Administrator', 'password': 'Administrator'}
    # @param proxies: Proxy definition
    # @param proxy_exceptions: Exception rules for proxy
    # @param repository: Repository to use by default
    # @param timeout: Client timeout
    # @param blob_timeout: Binary download timeout
    # @param cookie_jar: Cookie storage
    # @param upload_tmp_dir: Tmp file to use for buffering
    # @param check_suspended: Method to call while doing network call so you can interrupt the download thread
    # @param api_path: Default API Path
    def __init__(self, base_url="http://localhost:8080/nuxeo", auth=None, proxies=None, proxy_exceptions=None, repository="default",
                 timeout=20, blob_timeout=60, cookie_jar=None,
                 upload_tmp_dir=None, check_suspended=None, api_path="api/v1/"):
        self._headers = {}
        # Function to check during long-running processing like upload /
        # download if the synchronization thread needs to be suspended
        self.check_suspended = check_suspended

        if timeout is None or timeout < 0:
            timeout = 20
        self.timeout = timeout
        socket.setdefaulttimeout(self.timeout)
        # Dont allow null timeout
        if blob_timeout is None or blob_timeout < 0:
            blob_timeout = 60
        self.blob_timeout = blob_timeout

        self.upload_tmp_dir = (upload_tmp_dir if upload_tmp_dir is not None
                               else tempfile.gettempdir())

        if not base_url.endswith('/'):
            base_url += '/'
        self._base_url = base_url
        if not api_path.endswith('/'):
            api_path += '/'

        self._repository = repository
        self.user_id = None
        self._auth = ['', '']
        self._update_auth(auth=auth)
        self.cookie_jar = cookie_jar
        cookie_processor = urllib2.HTTPCookieProcessor(
            cookiejar=cookie_jar)

        # Get proxy handler
        proxy_handler = get_proxy_handler(proxies,
                                          proxy_exceptions=proxy_exceptions,
                                          url=self._base_url)

        # Build URL openers
        #self.opener = urllib2.build_opener(cookie_processor, proxy_handler)
        self.streaming_opener = urllib2.build_opener(cookie_processor,
                                                     proxy_handler,
                                                     *get_handlers())
        self.opener = self.streaming_opener
        # Set Proxy flag
        self.is_proxy = False
        opener_proxies = get_opener_proxies(self.opener)
        if opener_proxies:
            self.is_proxy = True

        self.automation_url = base_url + 'site/automation/'
        self.batch_upload_url = 'batch/upload'
        self.batch_execute_url = 'batch/execute'

        # New batch upload API
        self.new_upload_api_available = True
        self._rest_url = base_url + api_path
        self.batch_upload_path = 'upload'
        self.operations = None


    def login(self):
        """Try to login and return the user.

        :return: Current user
        """
        self.execute('login', check_params=False)
        return self.users().fetch(self.user_id)

    def repository(self, name='default', schemas=[]):
        """
        :return: A repository object
        """
        return Repository(name, self, schemas=schemas)

    def directory(self, name):
        """
        :return: An Operation object
        """
        return Directory(name, self)

    def operation(self, name):
        """https://doc.nuxeo.com/display/NXDOC/Automation

        :return: An Operation object to perform on Automation
        """
        return Operation(name, self)

    def workflows(self):
        """
        :return: The Workflows service
        """
        return Workflows(self)

    def users(self):
        """
        :return: The Users service
        """
        return Users(self)

    def groups(self):
        """
        :return: The Groups service
        """
        return Groups(self)

    def batch_upload(self):
        """
        :return: Return a bucket to upload document to Nuxeo server
        """
        return BatchUpload(self)

    def request_authentication_token(self, application_name, device_id, device_description, permission, revoke=False):
        """Request and return a new token for the user
        Token requires to have an application name and device id and permission the description is optional
        Once the token received you can use it for future login
        """
        base_error_message = (
            "Failed to connect to Nuxeo server %s with user %s"
            " to acquire a token"
        ) % (self._base_url, self.user_id)

        parameters = {
            'deviceId': device_id,
            'applicationName': application_name,
            'permission': permission,
            'revoke': 'true' if revoke else 'false',
        }
        if device_description:
            parameters['deviceDescription'] = device_description
        url = self._base_url + 'authentication/token?'
        url += urlencode(parameters)

        headers = self._get_common_headers()
        cookies = self._get_cookies()
        self.trace("Calling %s with headers %r and cookies %r",
                url, headers, cookies)
        req = urllib2.Request(url, headers=headers)
        try:
            token = self.opener.open(req, timeout=self.timeout).read()
        except urllib2.HTTPError as e:
            if e.code == 401 or e.code == 403:
                raise Unauthorized(self._base_url, self.user_id, e.code)
            elif e.code == 404:
                # Token based auth is not supported by this server
                return None
            else:
                e.msg = base_error_message + ": HTTP error %d" % e.code
                raise e
        except Exception as e:
            if hasattr(e, 'msg'):
                e.msg = base_error_message + ": " + e.msg
            raise
        cookies = self._get_cookies()
        self.trace("Got token '%s' with cookies %r", token, cookies)
        # Use the (potentially re-newed) token from now on
        if not revoke:
            self._update_auth(token=token)
        return token

    def header(self, name, value):
        """Define a header.

        :param name: -- Header name
        :param value: -- Header value
        """
        self._headers[name] = value

    def headers(self, extras=None):
        """Return the headers that will be sent to the server
        You can set additional headers with extras argument.

        :param extras: -- a dictionary or object of additional headers to set
        """
        headers = self._get_common_headers()
        if extras is not None:
            self._headers.update(extras)
        headers.update(self._headers)
        return headers

    def _get_common_headers(self):
        """Headers to include in every HTTP requests

        Includes the authentication heads (token based or basic auth if no
        token).

        Also include an application name header to make it possible for the
        server to compute access statistics for various client types (e.g.
        browser vs devices).

        """
        headers = {
            'Cache-Control': 'no-cache'
        }
        if self._auth is not None:
            headers.update([self._auth])
        headers.update(self._headers)
        return headers

    def fetch_api(self):
        base_error_message = (
            "Failed to connect to Nuxeo server %s"
        ) % (self._base_url)
        url = self.automation_url
        headers = self._get_common_headers()
        cookies = self._get_cookies()
        self.trace("Calling %s with headers %r and cookies %r",
            url, headers, cookies)
        req = urllib2.Request(url, headers=headers)
        try:
            response = json.loads(self.opener.open(
                req, timeout=self.timeout).read())
        except urllib2.HTTPError as e:
            if e.code == 401 or e.code == 403:
                raise Unauthorized(self._base_url, self.user_id, e.code)
            else:
                msg = base_error_message + "\nHTTP error %d" % e.code
                if hasattr(e, 'msg'):
                    msg = msg + ": " + e.msg
                e.msg = msg
                raise e
        except urllib2.URLError as e:
            msg = base_error_message
            if hasattr(e, 'message') and e.message:
                e_msg = force_decode(": " + e.message)
                if e_msg is not None:
                    msg = msg + e_msg
            elif hasattr(e, 'reason') and e.reason:
                if (hasattr(e.reason, 'message')
                    and e.reason.message):
                    e_msg = force_decode(": " + e.reason.message)
                    if e_msg is not None:
                        msg = msg + e_msg
                elif (hasattr(e.reason, 'strerror')
                    and e.reason.strerror):
                    e_msg = force_decode(": " + e.reason.strerror)
                    if e_msg is not None:
                        msg = msg + e_msg
            if self.is_proxy:
                msg = (msg + "\nPlease check your Internet connection,"
                       + " make sure the Nuxeo server URL is valid"
                       + " and check the proxy settings.")
            else:
                msg = (msg + "\nPlease check your Internet connection"
                       + " and make sure the Nuxeo server URL is valid.")
            e.msg = msg
            raise e
        except Exception as e:
            msg = base_error_message
            if hasattr(e, 'msg'):
                msg = msg + ": " + e.msg
            e.msg = msg
            raise e
        self.operations = {}
        for operation in response["operations"]:
            self.operations[operation['id']] = operation
            op_aliases = operation.get('aliases')
            if op_aliases:
                for op_alias in op_aliases:
                    self.operations[op_alias] = operation

    def execute(self, command, url=None, op_input=None, timeout=-1,
                check_params=True, void_op=False, extra_headers=None,
                file_out=None, **params):
        """Execute an Automation operation

        :param command: operation to execute
        :param url: overrides the default url resolver
        :param op_input: operation input
        :param timeout: operation timeout
        :param check_params: verify that the params are valid on the client side
        :param void_op: If operation is a void operation
        :param extra_headers: Headers to add to the request
        :param file_out: Output result inside this file
        :param **params: any additional param to add to the request"""
        if 'params' in params:
            params = params['params']
        if check_params:
            self._check_params(command, params)

        if url is None:
            url = self.automation_url + command
        headers = {
            "Content-Type": "application/json+nxrequest",
            "Accept": "application/json+nxentity, */*",
            "X-NXproperties": "*",
            # Keep compatibility with old header name
            "X-NXDocumentProperties": "*",
        }
        if void_op:
            headers.update({"X-NXVoidOperation": "true"})
        headers.update({"X-NXRepository": self._repository})
        if extra_headers is not None:
            headers.update(extra_headers)
        headers.update(self._get_common_headers())

        json_struct = {'params': {}}
        for k, v in params.items():
            if v is None:
                continue
            if k == 'properties':
                s = ""
                for propname, propvalue in v.items():
                    s += "%s=%s\n" % (propname, propvalue)
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
        current_action = self._get_action()
        if current_action and current_action.progress is None:
            current_action.progress = 0
        if file_out is not None:
            locker = self.unlock_path(file_out)
            try:
                with open(file_out, "wb") as f:
                    while True:
                        # Check if synchronization thread was suspended
                        if self.check_suspended is not None:
                            self.check_suspended('File download: %s'
                                                 % file_out)
                        buffer_ = resp.read(self.get_download_buffer())
                        if buffer_ == '':
                            break
                        if current_action:
                            current_action.progress += (
                                                self.get_download_buffer())
                        f.write(buffer_)
                return None, file_out
            finally:
                self.lock_path(file_out, locker)
        else:
            return self._read_response(resp, url)

    def trace(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def _create_action(self, type, path, name):
        return {}

    def _get_action(self):
        return None

    def _end_action(self):
        pass

    def _update_auth(self, auth=None, password=None, token=None):
        """
        When username retrieved from database, check for unicode and convert to string.
        Note: base64Encoding for unicode type will fail, hence converting to string
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
            self._auth = ("Authorization", basic_auth)
        else:
            raise ValueError("Either password or token must be provided")

    def _get_cookies(self):
        return list(self.cookie_jar) if self.cookie_jar is not None else []

    def _check_operation(self, command):
        if self.operations is None:
            self.fetch_api()
        if command not in self.operations:
            raise ValueError("'%s' is not a registered operations." % command)
        return self.operations[command]

    def _check_params(self, command, params):
        method = self._check_operation(command)

        required_params = []
        other_params = []
        for param in method['params']:
            if param['required']:
                required_params.append(param['name'])
            else:
                other_params.append(param['name'])

        for param in params.keys():
            if (not param in required_params
                and not param in other_params):
                self.trace("Unexpected param '%s' for operation '%s'", param,
                            command)
        for param in required_params:
            if not param in params:
                raise ValueError(
                    "Missing required param '%s' for operation '%s'" % (
                        param, command))

        # TODO: add typechecking

    def request(self, relative_url, body=None, adapter=None, timeout=-1, method='GET', content_type="application/json",
                extra_headers=None, raw_body=False, query_params=dict()):
        """Execute a REST API call

        :param relative_url: url to call relative to the rest_url provide in constructor
        :param body: body of the request
        :param adpater: if specified will add the @adapter at the end of the url
        :param timeout: timeout
        :param method: HTTP method to use
        :param content_type: For the request
        :param extra_headers: Additional headers to send
        :param raw_body: Avoid any processing on the body, by default body are serialize to json
        :param query_params: Dict of the query parameter to add to the request ?param1=value1&param2=value2"""

        url = self._rest_url + relative_url
        if adapter is not None:
            url += '/@' + adapter

        if (len(query_params)):
            url += "?" + urlencode(query_params)

        if body is not None and not isinstance(body, str) and not raw_body:
            body = json.dumps(body, default=json_helper)

        headers = {
            "Content-Type": content_type,
            "Accept": "application/json+nxentity, */*",
        }
        headers.update(self._get_common_headers())
        if extra_headers is not None:
            headers.update(extra_headers)
        cookies = self._get_cookies()
        self.trace("Calling REST API %s with headers %r and cookies %r", url,
                  headers, cookies)
        req = Request(url, headers=headers, method=method, data=body)
        timeout = self.timeout if timeout == -1 else timeout
        try:
            resp = self.opener.open(req, timeout=timeout)
        except Exception as e:
            self._log_details(e)
            raise

        return self._read_response(resp, url)

    def _log_details(self, e):
        if hasattr(e, "fp"):
            detail = e.fp.read()
            try:
                exc = json.loads(detail)
                message = exc.get('message')
                stack = exc.get('stack')
                error = exc.get('error')
                if message:
                    self.debug('Remote exception message: %s', message)
                if stack:
                    self.debug('Remote exception stack: %r', exc['stack'], exc_info=True)
                else:
                    self.debug('Remote exception details: %r', detail)
                return exc.get('status'), exc.get('code'), message, error
            except:
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
        if content_type.startswith("application/json"):
            self.trace("Response for '%s' with cookies %r: %r",
                url, cookies, s)
            return json.loads(s) if s else None
        else:
            self.trace("Response for '%s' with cookies %r has content-type %r",
                url, cookies, content_type)
            return s
