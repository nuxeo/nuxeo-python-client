# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Group

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Dict, Optional, Text  # noqa
        from .client import NuxeoClient  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for groups. """
    def __init__(self, client, endpoint='group', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        self.query = '?fetch.group=memberUsers&fetch.group=memberGroups'
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Group, headers=headers)

    def get(self, group_id=None):
        # type: (Optional[Text]) -> Group
        """
        Get the detail of a group.

        :param group_id: the id of the group
        :return: the group
        """
        request_path = '{}{}'.format(group_id, self.query)
        return super(API, self).get(path=request_path)

    def post(self, group):
        # type: (Group) -> Group
        """
        Create a group.

        :param group: the group to create
        :return: the created group
        """
        return super(API, self).post(resource=group, path=self.query)

    create = post  # Alias for clarity

    def put(self, group):
        # type: (Group) -> Group
        """
        Update a group.

        :param group: the group to update
        :return: the updated group
        """
        return super(API, self).put(group)

    def delete(self, group_id):
        # type: (Text) -> None
        """
        Delete a group.

        :param group_id: the id of the group to delete
        """
        super(API, self).delete(group_id)
