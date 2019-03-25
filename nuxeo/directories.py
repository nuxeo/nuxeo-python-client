# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .exceptions import BadQuery
from .models import Directory, DirectoryEntry

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, Text, Optional, Union  # noqa
        from .client import NuxeoClient  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for directories. """
    def __init__(self, client, endpoint='directory', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=DirectoryEntry, headers=headers)

    def get(self, dir_name, dir_entry=None):
        # type: (Text, Optional[Text]) -> Union[Directory, DirectoryEntry]
        """
        Get the entries of a directory.

        If dir_entry is not None, return the corresponding entry.

        :param dir_name: the name of the directory
        :param dir_entry: the name of an entry
        :return: the directory entries
        """
        path = dir_name
        if dir_entry:
            path = '{}/{}'.format(path, dir_entry)

        entries = super(API, self).get(path=path)
        if dir_entry:
            return entries
        return Directory(directoryName=dir_name, entries=entries, service=self)

    def post(self, resource=None, dir_name=None, **kwargs):
        # type: (DirectoryEntry, Text, Any) -> DirectoryEntry
        """
        Create a directory entry.

        :param resource: the entry to create
        :param dir_name: the name of the directory
        :return: the created entry
        """
        if dir_name:
            if not isinstance(resource, DirectoryEntry):
                raise BadQuery('The resource should be a directory entry.')
            resource.directoryName = dir_name
        return super(API, self).post(resource=resource, path=dir_name)

    create = post  # Alias for clarity

    def put(self, resource, dir_name):
        # type: (DirectoryEntry, Text) -> DirectoryEntry
        """
        Update an entry.

        :param resource: the entry to update
        :param dir_name: the name of the directory
        :return: the updated entry
        """
        path = '{}/{}'.format(dir_name, resource.uid)
        return super(API, self).put(resource, path=path)

    def delete(self, dir_name, dir_entry):
        # type: (Text, Text) -> None
        """
        Delete a directory entry.

        :param dir_name: the name of the directory
        :param dir_entry: the name of the entry
        """
        path = '{}/{}'.format(dir_name, dir_entry)
        super(API, self).delete(path)

    def exists(self, dir_name, dir_entry=None):
        # type: (Text, Optional[Text]) -> bool
        """
        Check if a directory or an entry exists.

        :param dir_name: the name of the directory
        :param dir_entry: the name of the entry
        :return: True if it exists, else False
        """
        path = dir_name
        if dir_entry:
            path = '{}/{}'.format(path, dir_entry)
        return super(API, self).exists(path)
