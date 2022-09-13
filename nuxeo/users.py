# coding: utf-8
from typing import TYPE_CHECKING, Dict, Optional

from .endpoint import APIEndpoint
from .models import User

if TYPE_CHECKING:
    from .client import NuxeoClient


class API(APIEndpoint):
    """Endpoint for users."""

    __slots__ = ()

    def __init__(self, client, endpoint="user", headers=None):
        # type: (NuxeoClient, str, Optional[Dict[str, str]]) -> None
        super().__init__(client, endpoint=endpoint, cls=User, headers=headers)

    def get(self, user_id=None, ssl_verify=None):
        """
        Get the detail of a user.

        :param user_id: the id of the user
        :return: the user
        """
        if ssl_verify is False:
            return super().get(path=user_id, ssl_verify=False)
        else:
            return super().get(path=user_id)

    def post(self, user, ssl_verify=None):
        """
        Create a user.

        :param user: the user to create
        :return: the created user
        """
        if ssl_verify is False:
            return super().post(user, ssl_verify=False)
        else:
            return super().post(user)

    create = post  # Alias for clarity

    def put(self, user, ssl_verify=None):
        """
        Update a user.

        :param user: the user to update
        :return: the updated user
        """
        if ssl_verify is False:
            return super().put(user, ssl_verify=False)
        else:
            return super().put(user)

    def delete(self, user_id, ssl_verify=None):
        """
        Delete a user.

        :param user_id: the id of the user to delete
        """
        if ssl_verify is False:
            super().delete(user_id, ssl_verify=False)
        else:
            super().delete(user_id)

    def current_user(self, ssl_verify=True):
        """
        Get the current user details and validate the connection to the server at the same time.

        :return User: user's details
        """
        details = self.client.request(
            "GET", "site/api/v1/me", ssl_verify=ssl_verify
        ).json()
        return User(**details)
