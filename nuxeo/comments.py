# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Comment

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text
        from .client import NuxeoClient
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for comments. """

    __slots__ = ()

    def __init__(self, client, endpoint="id", headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Comment, headers=headers
        )

    def get(self, docuid, uid=None, params=None):
        # type: (Text, Text, Any) -> Comment
        """
        Get the detail of a comment.

        :param uid: the ID of the comment
        :return: the comment
        """
        path = "{}/@comment".format(docuid)
        if uid:
            path += "/{}".format(uid)

        # Adding "&fetch-comment=repliesSummary" to the URL to retrieve replies number as well
        kwargs = {"fetch-comment": "repliesSummary"}
        if isinstance(params, dict):
            kwargs.update(params)

        return super(API, self).get(path=path, params=kwargs)

    def post(self, docuid, text):
        # type: (Text, Text) -> Comment
        """
        Create a comment.

        :param comment: the comment to create
        :return: the created comment
        """
        kwargs = {"entity-type": "comment", "parentId": docuid, "text": text}
        return super(API, self).post(path=docuid, adapter="comment", resource=kwargs)

    create = post  # Alias for clarity

    def put(self, comment):
        # type: (Comment) -> None
        """
        Update a comment.

        :param resource: the entry to update
        :return: the entry updated
        """
        path = "{}/@comment/{}".format(comment.parentId, comment.uid)
        return super(API, self).put(resource=comment, path=path)

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
        # Adding "&fetch-comment=repliesSummary" to the URL to retrieve replies number as well
        kwargs = {"fetch-comment": "repliesSummary"}
        if isinstance(params, dict):
            kwargs.update(params)

        return super(API, self).get(path=uid, adapter="comment", params=kwargs)
