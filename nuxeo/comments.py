# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Comment
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text  # noqa
        from .client import NuxeoClient  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for comments. """

    def __init__(self, client, endpoint="@comment", headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Comment, headers=headers
        )

    def get(self, uid):
        # type: (Text) -> Comment
        """
        Get the detail of a comment.

        :param uid: the ID of the comment
        :return: the comment
        """
        # Adding "&fetch.comment=repliesSummary" to the URL to retrieve replies number as well
        return super(API, self).get(
            path=uid, params={"fetch.comment": "repliesSummary"}
        )

    def post(self, comment):
        # type: (Comment) -> Comment
        """
        Create a comment.

        :param comment: the comment to create
        :return: the created comment
        """
        return super(API, self).post(comment)

    create = post  # Alias for clarity

    def put(self, resource):
        # type: (Comment) -> None
        """
        Update a comment.

        :param resource: the entry to update
        :return: the entry updated
        """
        return super(API, self).put(resource)

    def delete(self, uid):
        # type: (Text) -> None
        """
        Delete a comment.

        :param uid: the ID of the comment to delete
        """
        super(API, self).delete(uid)

    def replies(self, uid, params=None):
        # type: (Text, Any) -> List[Comment]
        """
        Get the replies of the comment.

        Any additionnal arguments will be passed to the *params* parent's call.

        :param uid: the ID of the comment
        :return: the list of replies
        """
        # Adding "&fetch.comment=repliesSummary" to the URL to retrieve replies number as well
        kwargs = {"fetch.comment": "repliesSummary"}
        if isinstance(params, dict):
            kwargs.update(params)

        endpoint = "{}/id/{}/@comment".format(self.client.api_path, uid)

        with SwapAttr(self, "endpoint", endpoint):
            return super(API, self).get(params=kwargs)
