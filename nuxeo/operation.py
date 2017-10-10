# coding: utf-8
from __future__ import unicode_literals

from .blob import BatchBlob


class Operation(object):
    def __init__(self, nature, service):
        self._service = service
        self._type = nature
        self._params = dict()
        self._input = None

    def params(self, params=None):
        """
        Get or add parameters to the operation.

        :param params: To add if None this method behave as a getter.
        :return: The Operation parameters.
        """

        if params:
            self._params.update(params)
        return self._params

    def input(self, input_):
        """ Set the input for this operation. """
        self._input = input_

    def execute(self):
        """
        Execute the operation on the server.

        :return: Raw result from the server.
        """

        url = None
        input_ = self._input
        params = self._params
        if isinstance(input_, BatchBlob):
            url = (self._service._rest_url
                   + 'upload/'
                   + input_._service._batchid
                   + '/'
                   + str(input_.fileIdx)
                   + '/execute/'
                   + self._type)
            input_ = None
        return self._service.execute(
            self._type, url=url, params=params, op_input=input_)
