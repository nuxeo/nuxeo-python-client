# coding: utf-8
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .endpoint import APIEndpoint
from .models import Comment

if TYPE_CHECKING:
    from .client import NuxeoClient


class API(APIEndpoint):
    """ Endpoint for comments. """

    __slots__ = ()

    def __init__(self, client, endpoint="id", headers=None):
        # type: (NuxeoClient, str, Optional[Dict[str, str]]) -> None
        super().__init__(client, endpoint=endpoint, cls=Comment, headers=headers)

    def get(self, docuid, uid=None, params=None):
        # type: (str, str, Any) -> Comment
        """
        Get the detail of a comment.

        :param uid: the ID of the comment
        :return: the comment
        """
        path = f"{docuid}/@comment"
        if uid:
            path += f"/{uid}"

        # Adding "&fetch-comment=repliesSummary" to the URL to retrieve replies number as well
        kwargs = {"fetch-comment": "repliesSummary"}
        if isinstance(params, dict):
            kwargs.update(params)

        return super().get(path=path, params=kwargs)

    def post(self, docuid, text):
        # type: (str, str) -> Comment
        """
        Create a comment.

        :param comment: the comment to create
        :return: the created comment
        """
        kwargs = {"entity-type": "comment", "parentId": docuid, "text": text}
        return super().post(path=docuid, adapter="comment", resource=kwargs)

    create = post  # Alias for clarity

    def put(self, comment):
        # type: (Comment) -> None
        """
        Update a comment.

        :param resource: the entry to update
        :return: the entry updated
        """
        path = f"{comment.parentId}/@comment/{comment.uid}"
        return super().put(resource=comment, path=path)

    def delete(self, uid):
        # type: (str) -> None
        """
        Delete a comment.

        :param uid: the ID of the comment to delete
        """
        super().delete(uid)

    def replies(self, uid, params=None):
        # type: (str, Any) -> List[Comment]
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

        return super().get(path=uid, adapter="comment", params=kwargs)
