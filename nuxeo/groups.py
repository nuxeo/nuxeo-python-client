# coding: utf-8
from typing import TYPE_CHECKING, Dict, Optional

from .endpoint import APIEndpoint
from .models import Group

if TYPE_CHECKING:
    from .client import NuxeoClient


class API(APIEndpoint):
    """ Endpoint for groups. """

    __slots__ = ("params",)

    def __init__(self, client, endpoint="group", headers=None):
        # type: (NuxeoClient, str, Optional[Dict[str, str]]) -> None
        self.params = {"fetch-group": ["memberUsers", "memberGroups"]}
        super().__init__(client, endpoint=endpoint, cls=Group, headers=headers)

    def get(self, group_id=None):
        # type: (Optional[str]) -> Group
        """
        Get the detail of a group.

        :param group_id: the id of the group
        :return: the group
        """
        return super().get(path=group_id, params=self.params)

    def post(self, group):
        # type: (Group) -> Group
        """
        Create a group.

        :param group: the group to create
        :return: the created group
        """
        return super().post(resource=group, params=self.params)

    create = post  # Alias for clarity

    def put(self, group):
        # type: (Group) -> Group
        """
        Update a group.

        :param group: the group to update
        :return: the updated group
        """
        return super().put(group)

    def delete(self, group_id):
        # type: (str) -> None
        """
        Delete a group.

        :param group_id: the id of the group to delete
        """
        super().delete(group_id)
