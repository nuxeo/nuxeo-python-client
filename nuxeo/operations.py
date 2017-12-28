# coding: utf-8
from __future__ import unicode_literals

from collections import Sequence

from .compat import text
from .endpoint import APIEndpoint
from .models import Blob, Operation

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
}  # type = Dict[Text, Tuple[type, ...]])


class API(APIEndpoint):
    def __init__(self, client, endpoint='site/automation', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        self.operations = {}
        headers = headers or {}
        headers.update({
            'Content-Type': 'application/json+nxrequest',
            'X-NXproperties': '*'
        })
        super(API, self).__init__(
            client, endpoint=endpoint, cls=dict, headers=headers)
        self.endpoint = endpoint

    def get(self, **kwargs):
        return super(API, self).get()

    def new(self, command, **kwargs):
        # type: (Text, **Any) -> Operation
        return Operation(command=command, service=self, **kwargs)

    def execute(self,
                command,                # type: Text
                input_obj=None,         # type: Optional[Any]
                check_params=False,     # type: bool
                void_op=False,          # type: bool
                headers=None,           # type: Optional[Dict[Text, Text]]
                timeout=20,             # type: int
                file_out=None,          # type: Optional[Text]
                **params                # type: **Any
                ):
        # type: (...) -> Any
        """
        Execute an operation.

        :param command: the name of the operation
        :param input_obj: the input of the operation
        :param check_params: if True, parameters will
        be checked client-side
        :param void_op: if True, the body of the response
        from the server will be empty
        :param headers: extra HTTP headers
        :param timeout: the operation timeout
        :param file_out: if not None, path of the file
        where the response will be saved
        :param params: any other parameter
        :return: the result of the execution
        """

        if isinstance(input_obj, Blob):
            url = '{}/upload/{}/{}/execute/{}'.format(
                self.client.api_path, input_obj.batch_id,
                input_obj.fileIdx, command)
            input_obj = None
        else:
            url = 'site/automation/{}'.format(command)

        if 'params' in params:
            params = params['params']

        if check_params:
            self.check_params(command, params)

        headers = headers or {}
        if self.headers:
            headers.update(self.headers)
        if void_op:
            headers['X-NXVoidOperation'] = 'true'

        data = {'params': {}}
        for (k, v) in params.items():
            if v is None:
                continue
            if k == 'properties':
                if isinstance(v, dict):
                    s = '\n'.join(['{}={}'.format(name, value) for (name, value) in v.items()])
                else:
                    s = v
                data['params'][k] = s.strip()
            else:
                data['params'][k] = v

        if input_obj:
            if isinstance(input_obj, list):
                data['input'] = "docs:" + ",".join(input_obj)
            else:
                data['input'] = input_obj

        resp = self.client.request('POST', url, data=data, headers=headers, timeout=timeout)

        action = self.get_action()
        if action and action.progress is None:
            action.progress = 0

        if file_out:
            locker = self.lock_path(file_out)
            try:
                with open(file_out, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=self.client.chunk_size):
                        if action:
                            action.progress += self.client.chunk_size
                        f.write(chunk)
                return file_out
            finally:
                self.unlock_path(file_out, locker)
        else:
            try:
                return resp.json()
            except ValueError:
                return resp.content

    def put(self, resource, **kwargs):
        raise NotImplementedError

    def delete(self, resource_id):
        raise NotImplementedError

    @property
    def dict(self):
        """
        Get a dict of available operations.

        :return: the available operations
        """
        if not self.operations:
            self.operations = {}

            response = self.get()
            for operation in response['operations']:
                self.operations[operation['id']] = operation
                for alias in operation.get('aliases', []):
                    self.operations[alias] = operation

        return self.operations

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

        operation = self.dict.get(command)
        if not operation:
            raise ValueError('{!r} is not a registered operation'.format(command))

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

    def get_action(self):
        pass

    def lock_path(self, file_path):
        pass

    def unlock_path(self, file_path, locker):
        pass
