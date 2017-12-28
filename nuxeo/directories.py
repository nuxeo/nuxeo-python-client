# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Directory, DirectoryEntry


class API(APIEndpoint):
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
        request_path = dir_name
        if dir_entry:
            request_path = '{}/{}'.format(request_path, dir_entry)

        entries = super(API, self).get(request_path=request_path)
        if not dir_entry:
            return Directory(directoryName=dir_name, entries=entries, service=self)
        return entries

    def post(self,
             resource=None,     # type: Union[Directory, DirectoryEntry]
             dir_name=None,     # type: Optional[Text]
             **kwargs           # type: **Any
             ):
        # type: (...) -> Union[Directory, DirectoryEntry]
        """
        Create a directory or an entry.

        :param resource: the directory/entry to create
        :param dir_name: the name of the directory
        :return: the created directory/entry
        """
        if dir_name:
            if not isinstance(resource, DirectoryEntry):
                raise ValueError('The resource should be a directory entry.')
            resource.directoryName = dir_name
        return super(API, self).post(resource=resource, request_path=dir_name)

    def create(self,
               resource,        # type: Union[Directory, DirectoryEntry]
               dir_name,        # type: Text
               dir_entry=None   # type: Optional[Text]
               ):
        # type: (Text) -> resource
        """ Alias for post(). """
        return self.post(resource, dir_name, dir_entry=dir_entry)

    def put(self,
            resource,  # type: Union[Directory, DirectoryEntry]
            dir_name,  # type: Text
            dir_entry  # type: Optional[Text]
            ):
        # type: (...) -> Union[Directory, DirectoryEntry]
        """
        Update an entry.

        :param resource: the entry to update
        :param dir_name: the name of the directory
        :param dir_entry: the name of the entry
        :return: the updated entry
        """
        request_path = '{}/{}'.format(dir_name, dir_entry)
        return super(API, self).put(resource, request_path=request_path)

    def delete(self, dir_name, dir_entry=None):
        # type: (Text, Optional[Text]) -> Union[Directory, DirectoryEntry]
        """
        Delete a directory or an entry.

        :param dir_name: the name of the directory
        :param dir_entry: the name of the entry
        :return: the deleted directory/entry
        """
        request_path = dir_name
        if dir_entry:
            request_path = '{}/{}'.format(request_path, dir_entry)
        return super(API, self).delete(request_path)

    def exists(self, dir_name, dir_entry=None):
        # type: (Text, Optional[Text]) -> bool
        """
        Check if a directory or an entry exists.

        :param dir_name: the name of the directory
        :param dir_entry: the name of the entry
        :return: True if it exists, else False
        """
        request_path = dir_name
        if dir_entry:
            request_path = '{}/{}'.format(request_path, dir_entry)
        return super(API, self).exists(request_path)
