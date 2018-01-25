# coding: utf-8
from __future__ import unicode_literals

from collections import Sequence

from .compat import text
from .endpoint import APIEndpoint
from .exceptions import CorruptedFile
from .models import Blob, Operation
from .utils import get_digester

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from requests import Response
        from typing import Any, Dict, Optional, Text, Tuple, Type
        from .client import NuxeoClient
except ImportError:
    pass

PARAM_TYPES = {  # Types allowed for operations parameters
    'blob': (text, Blob),
    'boolean': (bool,),
    'date': (text,),
    'document': (text,),
    'documents': (list,),
    'int': (int,),
    'integer': (int,),
    'long': (int,),
    'map': (dict,),
    'object': (object,),
    'properties': (dict,),
    'resource': (text,),
    'serializable': (Sequence,),
    'string': (text,),
    'stringlist': (Sequence,),
    'validationmethod': (text,),
}  # type: Dict[Text, Tuple[Type, ...]]


class API(APIEndpoint):
    """ Endpoint for operations. """
    def __init__(self, client, endpoint='site/automation', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        self.ops = {}  # type: Dict[Text, Any]
        headers = headers or {}
        headers.update({
            'Content-Type': 'application/json+nxrequest',
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
            self.ops = {}

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

        :raises ValueError: When the `command` is not valid.
        :raises ValueError: On unexpected parameter.
        :raises ValueError: On missing required parameter.
        :raises TypeError: When a parameter has not the required type.
        """

        operation = self.operations.get(command)
        if not operation:
            raise ValueError(
                '{!r} is not a registered operation'.format(command))

        parameters = {param['name']: param for param in operation['params']}

        for (name, value) in params.items():
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
        for (name, parameter) in parameters.items():
            if parameter['required']:
                err = 'missing required parameter {!r} for operation {!r}'
                raise ValueError(err.format(name, command))

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
        command, input_obj, params = self.get_attributes(operation, **kwargs)

        if kwargs.pop('check_params', False):
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

        data = {'params': {}}  # type: Dict[Text, Any]
        for k, v in params.items():
            if v is None:
                continue

            if k != 'properties':
                data['params'][k] = v
                continue

            # v can only be a dict
            data['params'][k] = '\n'.join(['{}={}'.format(name, value)
                                           for name, value in v.items()])

        if input_obj:
            if isinstance(input_obj, list):
                input_obj = 'docs:' + ','.join(input_obj)
            data['input'] = input_obj

        default = kwargs.get('default', object)
        resp = self.client.request(
            'POST', url, data=data, headers=headers, default=default)

        # Save to a file, part by part of chunk_size
        if file_out:
            return self.save_to_file(operation, resp, file_out, **kwargs)

        # It is likely a JSON response we do not want to save to a file
        if operation:
            operation.progress = int(resp.headers.get('content-length', 0))

        try:
            return resp.json()
        except ValueError:
            return resp.content

    def get_attributes(self, operation, **kwargs):
        # type: (Operation, Any) -> (Text, Any, Dict[Text, Any])
        """ Get the operation attributes. """
        if operation:
            command = operation.command
            input_obj = operation.input_obj
            params = operation.params
        else:
            command = kwargs.pop('command', None)
            input_obj = kwargs.pop('input_obj', None)
            params = kwargs.pop('params', kwargs)
        return command, input_obj, params

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
        digester = get_digester(digest)

        with open(path, 'wb') as f:
            chunk_size = kwargs.get('chunk_size', self.client.chunk_size)
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if operation:
                    operation.progress += chunk_size
                f.write(chunk)
                if digester:
                    digester.update(chunk)

        if digester:
            actual_digest = digester.hexdigest()
            if digest != actual_digest:
                raise CorruptedFile(path, digest, actual_digest)

        return path
