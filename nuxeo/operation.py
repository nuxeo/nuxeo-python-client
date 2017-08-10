# coding: utf-8
from .blob import BatchBlob


class Operation(object):
    def __init__(self, type, service):
        self._service = service
        self._type = type
        self._params = dict()
        self._input = None

    def params(self, params=None):
        """
        Get or add parameters to the operation

        :param params: To add if None this method behave as a getter
        :return: The Operation parameters
        """
        if params is not None:
            for key in params:
                self._params[key] = params[key]
        return self._params

    def input(self, input):
        """
        Set the input for this operation
        """
        self._input = input

    def execute(self):
        """
        Execute the operation on the server
        :return: Raw result from the server
        """
        url = None
        input = self._input
        params = self._params
        if isinstance(input, BatchBlob):
            if input.compatibility_mode():
                params['batchId'] = input.get_batch_id()
                params['fileIdx'] = input.fileIdx
            else:
                url = self._service._rest_url + 'upload/' + input._service._batchid + '/' + str(input.fileIdx) + '/execute/' + self._type
                input = None
        return self._service.execute(self._type, url=url, params=params, op_input=input)