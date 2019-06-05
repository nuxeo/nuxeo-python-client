# coding: utf-8
from __future__ import unicode_literals
from os import fsync

try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence

from . import constants
from .compat import get_text, long, text
from .endpoint import APIEndpoint
from .exceptions import BadQuery, CorruptedFile
from .models import Blob, Operation
from .utils import get_digester

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from requests import Response  # noqa
        from typing import Any, Dict, Optional, Text, Tuple, Type  # noqa
        from .client import NuxeoClient  # noqa
except ImportError:
    pass

# Types allowed for operations parameters
# See https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html
# for default values
PARAM_TYPES = {
    # Operation: ((accepted types), default value if optional))
    'blob': ((text, bytes, Blob), None),
    'boolean': ((bool,), False),
    'date': ((text, bytes,), None),
    'document': ((text, bytes,), None),
    'documents': ((list,), None),
    'int': ((int,), 0),
    'integer': ((int,), 0),
    'long': ((int, long), 0),
    'list': ((list,), None),
    'map': ((dict,), None),
    'object': ((object,), None),
    'properties': ((dict,), None),
    'resource': ((text, bytes,), None),
    'serializable': ((Sequence,), None),
    'string': ((text, bytes,), None),
    'stringlist': ((Sequence,), None),
    'validationmethod': ((text, bytes,), None),
}  # type: Dict[Text, Tuple[Type, ...]]


class API(APIEndpoint):
    """ Endpoint for operations. """

    # Operations cache
    ops = {}  # type: Dict[Text, Any]

    def __init__(self, client, endpoint='site/automation', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        headers = headers or {}
        headers.update({
            'Content-Type': 'application/json',
            'X-NXproperties': '*'
        })
        super(API, self).__init__(
            client, endpoint=endpoint, cls=dict, headers=headers)
        self.endpoint = endpoint

    def get(self, **kwargs):
        # type: (Any) -> Dict[Text, Any]
        """ Get the list of available operations from the server. """
        return super(API, self).get()

    def put(self, **kwargs):
        # type: (Any) -> None
        raise NotImplementedError()

    def delete(self, resource_id):
        # type: (Text) -> None
        raise NotImplementedError()

    @property
    def operations(self):
        # type: () -> Dict[Text, Any]
        """
        Get a dict of available operations.

        :return: the available operations
        """
        if not self.ops:
            response = self.get()
            for operation in response['operations']:
                self.ops[operation['id']] = operation
                for alias in operation.get('aliases', []):
                    self.ops[alias] = operation

        return self.ops

    def check_params(self, command, params):
        # type: (Text, Dict[Text, Any]) -> None
        """
        Check given parameters of the `command` operation.  It will also
        check for types whenever possible.
        """

        operation = self.operations.get(command)
        if not operation:
            raise BadQuery(
                '{!r} is not a registered operation'.format(command))

        parameters = {param['name']: param for param in operation['params']}

        for name, value in params.items():
            # Check for unexpected parameters.  We use `dict.pop()` to
            # get and delete the parameter from the dict.
            try:
                param = parameters.pop(name)
            except KeyError:
                err = 'unexpected parameter {!r} for operation {}'
                raise BadQuery(err.format(name, command))

            # Check types
            types_accepted, default = PARAM_TYPES[param['type']]
            if not param['required']:
                # Allow the default value when the parameter is not required
                types_accepted += (type(default),)
            types_accepted = tuple(set(types_accepted))  # Uniquify

            if not isinstance(value, types_accepted):
                types = [type_.__name__ for type_ in types_accepted]
                if len(types) > 1:
                    types = ', '.join(types[:-1]) + ' or ' + types[-1]
                else:
                    types = types[0]
                err = ('parameter {}={!r} should be of type {}'
                       ' (current is {})')
                raise BadQuery(
                    err.format(name, value, types, type(value).__name__))

        # Check for required parameters.  As of now, `parameters` may contain
        # unclaimed parameters and we just need to check for required ones.
        for (name, parameter) in parameters.items():
            if parameter['required']:
                err = 'missing required parameter {!r} for operation {!r}'
                raise BadQuery(err.format(name, command))

    def execute(
        self,
        operation=None,  # type: Optional[Operation]
        void_op=False,  # type: bool
        headers=None,  # type: Optional[Dict[Text, Text]]
        file_out=None,  # type: Optional[Text]
        **kwargs  # type: Any
    ):
        # type: (...) -> Any
        """
        Execute an operation.

        If there is no operation parameter, the command,
        the input object, and the parameters of the operation
        will be taken from the kwargs.

        :param operation: the operation
        :param void_op: if True, the body of the response
        from the server will be empty
        :param headers: extra HTTP headers
        :param file_out: if not None, path of the file
        where the response will be saved
        :param kwargs: any other parameter
        :return: the result of the execution
        """
        json = kwargs.pop('json', True)
        callback = kwargs.pop('callback', None)
        enrichers = kwargs.pop('enrichers', None)

        command, input_obj, params, context = self.get_attributes(operation, **kwargs)

        if kwargs.pop('check_params', constants.CHECK_PARAMS):
            self.check_params(command, params)

        url = 'site/automation/{}'.format(command)
        if isinstance(input_obj, Blob):
            url = '{}/upload/{}/{}/execute/{}'.format(
                self.client.api_path, input_obj.batch_id,
                input_obj.fileIdx, command)
            input_obj = None

        headers = headers or {}
        headers.update(self.headers)
        if void_op:
            headers['X-NXVoidOperation'] = 'true'

        data = self.build_payload(params, context)

        if input_obj:
            if isinstance(input_obj, list):
                input_obj = 'docs:' + ','.join(input_obj)
            data['input'] = input_obj

        resp = self.client.request(
            'POST', url, data=data, headers=headers, enrichers=enrichers,
            default=kwargs.get('default', object))

        # Save to a file, part by part of chunk_size
        if file_out:
            return self.save_to_file(operation, resp, file_out,
                                     callback=callback, **kwargs)

        # It is likely a JSON response we do not want to save to a file
        if operation:
            operation.progress = int(resp.headers.get('content-length', 0))

        if json:
            try:
                return resp.json()
            except ValueError:
                pass
        return resp.content

    @staticmethod
    def get_attributes(operation, **kwargs):
        # type: (Operation, Any) -> (Text, Any, Dict[Text, Any])
        """ Get the operation attributes. """
        if operation:
            command = operation.command
            input_obj = operation.input_obj
            context = operation.context
            params = operation.params
        else:
            command = kwargs.pop('command', None)
            input_obj = kwargs.pop('input_obj', None)
            context = kwargs.pop('context', None)
            params = kwargs.pop('params', kwargs)
        return command, input_obj, params, context

    def build_payload(self, params, context):
        # type: (Dict[Text, Any], Dict[Text, Any]) -> Dict[Text, Any]
        """ Create sanitized operation payload. """
        data = {'params': self.sanitize(params)}  # type: Dict[Text, Any]
        clean_context = self.sanitize(context)  # type: Dict[Text, Any]
        if clean_context:
            data['context'] = clean_context

        return data

    @staticmethod
    def sanitize(obj):
        # type: (Dict[Text, Any]) -> Dict[Text, Any]
        """ Sanitize the operation parameters. """
        if not obj:
            return {}

        clean_obj = {}  # type: Dict[Text, Any]

        for k, v in obj.items():
            if v is None:
                continue

            if k != 'properties':
                clean_obj[k] = v
                continue

            # v can only be a dict
            contents = ['{}={}'.format(name, get_text(value))
                        for name, value in v.items()]
            clean_obj[k] = '\n'.join(contents)

        return clean_obj

    def new(self, command, **kwargs):
        # type: (Text, Any) -> Operation
        """ Make a new Operation object. """
        return Operation(command=command, service=self, **kwargs)

    def save_to_file(self, operation, resp, path, **kwargs):
        # type: (Operation, Response, Text, Any) -> Text
        """
        Save the result of an operation to a file.

        If there is a digest of the file to check
        against the server, it can be passed in
        the kwargs.
        :param operation: the operation
        :param resp: the response from the Platform
        :param path: the path to save the file to
        :param kwargs: additional parameters
        :return:
        """
        digest = kwargs.pop('digest', None)
        digester = get_digester(digest) if digest else None

        unlock_path = kwargs.pop('unlock_path', None)
        lock_path = kwargs.pop('lock_path', None)
        callback = kwargs.pop('callback', None)
        use_lock = callable(unlock_path) and callable(lock_path)
        locker = None

        if use_lock:
            locker = unlock_path(path)
        try:
            with open(path, 'ab') as f:
                chunk_size = kwargs.get('chunk_size', self.client.chunk_size)
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    # Check if synchronization thread was suspended
                    if callable(callback):
                        callback(path)
                    if operation:
                        operation.progress += chunk_size
                    f.write(chunk)
                    if digester:
                        digester.update(chunk)

                # Force write of file to disk
                f.flush()
                fsync(f.fileno())
        finally:
            if use_lock:
                lock_path(path, locker)

        if digester:
            computed_digest = digester.hexdigest()
            if digest != computed_digest:
                raise CorruptedFile(path, digest, computed_digest)

        return path
