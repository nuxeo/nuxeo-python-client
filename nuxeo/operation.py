__author__ = 'loopingz'
from blob import BatchBlob

class Operation(object):
    def __init__(self, type, service):
        self._service = service
        self._type = type
        self._params = dict()
        self._input = None

    def params(self, params=None):
        if params is not None:
            for key in params:
                self._params[key] = params[key]
        return self._params

    def input(self, input):
        self._input = input

    def execute(self):
        url = None
        input = self._input
        if isinstance(self._input, BatchBlob):
            url = self._service._rest_url + 'upload/' + input._service._batchid + '/' + str(input.fileIdx) + '/execute/' + self._type
            input = None
        return self._service.execute(self._type, url=url, params=self._params, op_input=input)