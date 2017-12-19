# coding: utf-8
from __future__ import unicode_literals

from typing import Any, Dict, List, Optional, Text, Union

from .blob import BlobInfo

__all__ = ('Operation',)


class Operation(object):
    def __init__(self, nature, service):
        # type: (Text, Nuxeo) -> None
        self.service = service
        self._type = nature
        self._params = dict()
        self._input = None

    def execute(self, **kwargs):
        # type: (**Any) -> Union[Dict[Text, Any], Text]
        """
        Execute the operation on the server.

        :param kwargs: Additional args forwarded to :meth:`Nuxeo.execute()`.
        :return: Raw result from the server.
        """

        url = None
        input_ = self._input
        params = self._params
        if isinstance(input_, BlobInfo):
            url = (self.service.rest_url
                   + 'upload/'
                   + input_.service.batchid
                   + '/'
                   + str(input_.fileIdx)
                   + '/execute/'
                   + self._type)
            input_ = None
        return self.service.execute(
            self._type, url=url, params=params, op_input=input_, **kwargs)

    def input(self, input_):
        # type: (Union[Text, List[Text], Dict[Text, Any]]) -> None
        """ Set the input for this operation. """
        self._input = input_

    def params(self, params=None):
        # type: (Optional[Dict[Text, Any]]) -> Dict[Text, Any]
        """
        Get or add parameters to the operation.

        :param params: To add if None this method behave as a getter.
        :return: The Operation parameters.
        """

        if params:
            self._params.update(params)
        return self._params
