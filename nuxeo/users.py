# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import User

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Dict, Optional, Text  # noqa
        from .client import NuxeoClient  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for users. """
    def __init__(self, client, endpoint='user', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=User, headers=headers)

    def get(self, user_id=None):
        # type: (Optional[Text]) -> User
        """
        Get the detail of a user.

        :param user_id: the id of the user
        :return: the user
        """
        return super(API, self).get(path=user_id)

    def post(self, user):
        # type: (User) -> User
        """
        Create a user.

        :param user: the user to create
        :return: the created user
        """
        return super(API, self).post(user)

    create = post  # Alias for clarity

    def put(self, user):
        # type: (User) -> User
        """
        Update a user.

        :param user: the user to update
        :return: the updated user
        """
        return super(API, self).put(user)

    def delete(self, user_id):
        # type: (Text) -> None
        """
        Delete a user.

        :param user_id: the id of the user to delete
        """
        super(API, self).delete(user_id)
