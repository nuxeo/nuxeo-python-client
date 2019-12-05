# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Comment

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Dict, Optional, Text  # noqa
        from .client import NuxeoClient  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for comments. """

    def __init__(
        self,
        client,  # type: NuxeoClient
        endpoint="@comment",  # type: Text
        headers=None,  # type: Optional[Dict[Text, Text]]
    ):
        # type: (...) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Comment, headers=headers
        )

    def get(self, uid=None, **params):
        # type: (Optional[Text], Any) -> Comment
        """
        Get the detail of a comment.

        Any additionnal arguments will be passed to the *params* parent's call.

        :param uid: the ID of the comment
        :return: the comment
        """
        return super(API, self).get(path=uid, params=params)

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
