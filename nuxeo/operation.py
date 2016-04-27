__author__ = 'loopingz'

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
        return self._service.execute(self._type, params=self._params, op_input=self._input)