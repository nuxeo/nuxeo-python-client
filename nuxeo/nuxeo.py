"""Common Nuxeo Automation client utilities."""

import sys
import base64
import json
import urllib2
import random
import time
import re
import os
import hashlib
import tempfile
from urllib import urlencode
from urllib2 import ProxyHandler
from urlparse import urlparse
from poster.streaminghttp import get_handlers
import socket

AUDIT_CHANGE_FINDER_TIME_RESOLUTION = 1.0

def guess_digest_algorithm(digest):
    # For now only md5 and sha1 are supported
    if digest is None or len(digest) == 32:
        return 'md5'
    elif len(digest) == 40:
        return 'sha1'
    else:
        raise Exception('Unknown digest algorithm for %s' % digest)

DEFAULT_NUXEO_TX_TIMEOUT = 60
# Default buffer size for file upload / download and digest computation
FILE_BUFFER_SIZE = 1024 ** 2


def safe_filename(name, replacement=u'-'):
    """Replace invalid character in candidate filename"""
    return re.sub(ur'(/|\\|\*|:|\||"|<|>|\?)', replacement, name)


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


class AddonNotInstalled(Exception):
    pass


class NewUploadAPINotAvailable(Exception):
    pass


class CorruptedFile(Exception):
    pass


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
    """Client for the Nuxeo Content Automation HTTP API

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

    def users(self):
        """
        :return: The users service
        """
        from users import Users
        return Users(self)

    def groups(self):
        """
        :return: The groups service
        """
        from groups import Groups
        return Groups(self)

    def operation(self, name):
        """
        :return: An Operation object
        """
        from operation import Operation
        return Operation(name, self)

    def directory(self, name):
        """
        :return: An Operation object
        """
        from directory import Directory
        return Directory(name, self)

    def batch_upload(self):
        from batchupload import BatchUpload
        return BatchUpload(self)

    def repository(self, name='default', schemas=[]):
        """
        :return: A repository object
        """
        from repository import Repository
        return Repository(name, self, schemas=schemas)

    def login(self):
        """Try to login and return the user.

        """
        self.execute('login', check_params=False)
        return self.users().fetch(self.user_id)

    def header(self, name, value):
        """Define a header.

        Keyword arguments:
        name -- Header name
        value -- Header value
        """
        self._headers[name] = value

    def headers(self, extras=None):
        """Return the headers that will be sent to the server
        You can set additional headers with extras argument.

        Keyword arguments:
        extras -- a dictionary or object of additional headers to set
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
        """Execute an Automation operation"""
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
        data = json.dumps(json_struct)

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

    def execute_with_blob_streaming(self, command, file_path, filename=None,
                                    mime_type=None, **params):
        """Execute an Automation operation using a batch upload as an input

        Upload is streamed.
        """
        tick = time.time()
        action = self._create_action("Upload", file_path, filename)
        try:
            batch_id = None
            if self.is_new_upload_api_available():
                try:
                    # Init resumable upload getting a batch id generated by the server
                    # This batch id is to be used as a resumable session id
                    batch_id = self.init_upload()['batchId']
                except NewUploadAPINotAvailable:
                    self.debug('New upload API is not available on server %s', self._base_url)
                    self.new_upload_api_available = False
            if batch_id is None:
                # New upload API is not available, generate a batch id
                batch_id = self._generate_unique_id()
            upload_result = self.upload(batch_id, file_path, filename=filename,
                                        mime_type=mime_type)
            upload_duration = int(time.time() - tick)
            action.transfer_duration = upload_duration
            # Use upload duration * 2 as Nuxeo transaction timeout
            tx_timeout = max(DEFAULT_NUXEO_TX_TIMEOUT, upload_duration * 2)
            self.trace('Using %d seconds [max(%d, 2 * upload time=%d)] as Nuxeo'
                      ' transaction timeout for batch execution of %s'
                      ' with file %s', tx_timeout, DEFAULT_NUXEO_TX_TIMEOUT,
                      upload_duration, command, file_path)
            # NXDRIVE-433: Compat with 7.4 intermediate state
            if upload_result.get('uploaded') is None:
                self.new_upload_api_available = False
            if upload_result.get('batchId') is not None:
                result = self.execute_batch(command, batch_id, '0', tx_timeout,
                                          **params)
                return result
            else:
                raise ValueError("Bad response from batch upload with id '%s'"
                                 " and file path '%s'" % (batch_id, file_path))
        except InvalidBatchException:
            self.cookie_jar.clear_session_cookies()
        finally:
            self._end_action()

    def trace(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass
    '''
    def upload(self, batch_id, file_path, filename=None, file_index=0,
               mime_type=None):
        """Upload a file through an Automation batch

        Uses poster.httpstreaming to stream the upload
        and not load the whole file in memory.
        """
        self._create_action("Upload", file_path, filename)
        # Request URL
        if self.is_new_upload_api_available():
            url = self._rest_url + self.batch_upload_path + '/' + batch_id + '/' + str(file_index)
        else:
            # Backward compatibility with old batch upload API
            url = self.automation_url.encode('ascii') + self.batch_upload_url

        if not self.is_new_upload_api_available():
            headers.update({"X-Batch-Id": batch_id, "X-File-Idx": file_index})
        headers.update(self._get_common_headers())

        # Request data
        input_file = open(file_path, 'rb')
        # Use file system block size if available for streaming buffer
        fs_block_size = self.get_upload_buffer(input_file)
        data = self._read_data(input_file, fs_block_size)

        # Execute request
        cookies = self._get_cookies()
        self.trace("Calling %s with headers %r and cookies %r for file %s",
            url, headers, cookies, file_path)
        req = urllib2.Request(url, data, headers)
        try:
            resp = self.streaming_opener.open(req, timeout=self.blob_timeout)
        except Exception as e:
            log_details = self._log_details(e)
            if isinstance(log_details, tuple):
                _, _, _, error = log_details
                if error and error.startswith("Unable to find batch"):
                    raise InvalidBatchException()
            raise e
        finally:
            input_file.close()
        self._end_action()
        return self._read_response(resp, url)
    '''

    def _create_action(self, type, path, name):
        return {}

    def _get_action(self):
        return None

    def _end_action(self):
        pass

    def execute_batch(self, op_id, batch_id, file_idx, tx_timeout, **params):
        """Execute a file upload Automation batch"""
        extra_headers = {'Nuxeo-Transaction-Timeout': tx_timeout, }
        if self.is_new_upload_api_available():
            url = (self._rest_url + self.batch_upload_path + '/' + batch_id + '/' + file_idx
                   + '/execute/' + op_id)
            return self.execute(None, url=url, timeout=tx_timeout,
                                check_params=False, extra_headers=extra_headers, **params)
        else:
            return self.execute(self.batch_execute_url, timeout=tx_timeout,
                                operationId=op_id, batchId=batch_id, fileIdx=file_idx,
                                check_params=False, extra_headers=extra_headers, **params)

    def is_addon_installed(self):
        return 'NuxeoDrive.GetRoots' in self.operations

    def is_event_log_id_available(self):
        return self.is_event_log_id

    def is_elasticsearch_audit(self):
        return 'NuxeoDrive.WaitForElasticsearchCompletion' in self.operations

    def is_nuxeo_drive_attach_blob(self):
        return 'NuxeoDrive.AttachBlob' in self.operations

    def is_new_upload_api_available(self):
        return self.new_upload_api_available

    def request_authentication_token(self, application_name, device_id, device_description, permission, revoke=False):
        """Request and return a new token for the user"""
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

    def wait(self):
        # Used for tests
        if self.is_elasticsearch_audit():
            self.execute("NuxeoDrive.WaitForElasticsearchCompletion")
        else:
            # Backward compatibility with JPA audit implementation,
            # in which case we are also backward compatible with date based resolution
            if not self.is_event_log_id_available():
                time.sleep(AUDIT_CHANGE_FINDER_TIME_RESOLUTION)
            self.execute("NuxeoDrive.WaitForAsyncCompletion")

    def make_tmp_file(self, content):
        """Create a temporary file with the given content for streaming upload purpose.

        Make sure that you remove the temporary file with os.remove() when done with it.
        """
        fd, path = tempfile.mkstemp(suffix=u'-nxdrive-file-to-upload',
                                   dir=self.upload_tmp_dir)
        with open(path, "wb") as f:
            f.write(content)
        os.close(fd)
        return path

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

    def _generate_unique_id(self):
        """Generate a unique id based on a timestamp and a random integer"""

        return str(time.time()) + '_' + str(random.randint(0, 1000000000))

    def do_get(self, url, file_out=None, digest=None, digest_algorithm=None):
        self.trace('Downloading file from %r to %r with digest=%s, digest_algorithm=%s', url, file_out, digest,
                  digest_algorithm)
        h = None
        if digest is not None:
            if digest_algorithm is None:
                digest_algorithm = guess_digest_algorithm(digest)
                self.trace('Guessed digest algorithm from digest: %s', digest_algorithm)
            digester = getattr(hashlib, digest_algorithm, None)
            if digester is None:
                raise ValueError('Unknow digest method: ' + digest_algorithm)
            h = digester()
        headers = self._get_common_headers()
        base_error_message = (
            "Failed to connect to Nuxeo server %r with user %r"
        ) % (self._base_url, self.user_id)
        try:
            self.trace("Calling '%s' with headers: %r", url, headers)
            req = urllib2.Request(url, headers=headers)
            response = self.opener.open(req, timeout=self.blob_timeout)
            current_action = self._get_action()
            # Get the size file
            if (current_action and response is not None
                and response.info() is not None):
                current_action.size = int(response.info().getheader(
                                                    'Content-Length', 0))
            if file_out is not None:
                locker = self.unlock_path(file_out)
                try:
                    with open(file_out, "wb") as f:
                        while True:
                            # Check if synchronization thread was suspended
                            if self.check_suspended is not None:
                                self.check_suspended('File download: %s'
                                                     % file_out)
                            buffer_ = response.read(self.get_download_buffer())
                            if buffer_ == '':
                                break
                            if current_action:
                                current_action.progress += (
                                                    self.get_download_buffer())
                            f.write(buffer_)
                            if h is not None:
                                h.update(buffer_)
                    if digest is not None:
                        actual_digest = h.hexdigest()
                        if digest != actual_digest:
                            if os.path.exists(file_out):
                                os.remove(file_out)
                            raise CorruptedFile("Corrupted file %r: expected digest = %s, actual digest = %s"
                                                % (file_out, digest, actual_digest))
                    return None, file_out
                finally:
                    self.lock_path(file_out, locker)
            else:
                result = response.read()
                if h is not None:
                    h.update(result)
                    if digest is not None:
                        actual_digest = h.hexdigest()
                        if digest != actual_digest:
                            raise CorruptedFile("Corrupted file: expected digest = %s, actual digest = %s"
                                                % (digest, actual_digest))
                return result, None
        except urllib2.HTTPError as e:
            if e.code == 401 or e.code == 403:
                raise Unauthorized(self._base_url, self.user_id, e.code)
            else:
                e.msg = base_error_message + ": HTTP error %d" % e.code
                raise e
        except Exception as e:
            if hasattr(e, 'msg'):
                e.msg = base_error_message + ": " + e.msg
            raise

    def get_download_buffer(self):
        return FILE_BUFFER_SIZE

    def request(self, relative_url, body=None, adapter=None, timeout=-1, method='GET', content_type="application/json", extra_headers=None, raw_body=False):
        """Execute a REST API call"""

        url = self._rest_url + relative_url
        if adapter is not None:
            url += '/@' + adapter

        if body is not None and not isinstance(body, str) and not raw_body:
            body = json.dumps(body)

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
