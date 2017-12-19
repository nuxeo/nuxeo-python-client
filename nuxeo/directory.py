# coding: utf-8
from __future__ import unicode_literals

from typing import Any, Dict, List, Optional, Text

from .common import NuxeoObject, NuxeoService

__all__ = ('Directory', 'DirectoryEntry')


class DirectoryEntry(NuxeoObject):
    """ Representation of an entry in a directory. """

    entity_type = 'directoryEntry'

    def __init__(self, obj, service=None):
        # type: (Dict[Text, Any], Optional[NuxeoService]) -> None
        super(DirectoryEntry, self).__init__(obj, service)
        self._entity_type = 'directoryEntry'
        self.directoryName = obj['directoryName']

    def get_id(self):
        # type: () -> Text
        return self.properties['id']


class Directory(NuxeoService):
    """ Directory service allow you to modify a Directory on the server. """

    def __init__(self, name, nuxeo):
        # type: (Text, Nuxeo) -> None
        super(Directory, self).__init__(nuxeo, 'group', DirectoryEntry)
        self._name = name
        self._path = 'directory/' + name

    def create(self, obj):
        # type: (NuxeoObject) -> NuxeoObject
        """
        Create a new entry in the directory.

        :param obj: a object with properties attribute or a dict
        :return: The new created entry
        """

        if isinstance(obj, self._object_class):
            properties = obj.properties
        elif isinstance(obj, dict):
            properties = obj
        else:
            err = 'Need a dictionary of properties or a object'
            raise ValueError(err.format(self._object_class))

        body = {
            'entity-type': self._object_class.entity_type,
            'directoryName': self._name,
            'properties': properties,
        }
        req = self._nuxeo.request(self._path, method='POST', body=body)
        return self._object_class(req, self)

    def fetch_all(self):
        # type: () -> List[DirectoryEntry]
        """
        :return: all entries from the Directory
        """
        result = self._nuxeo.request(self._path)
        return [DirectoryEntry(entry, self) for entry in result['entries']]

    def update(self, obj):
        # type: (NuxeoObject) -> None
        """ Update an entry in the directory. """

        body = {
            'entity-type': self._object_class.entity_type,
            'properties': obj.properties,
            'directoryName': self._name,
        }
        self._nuxeo.request(
            self._path + '/' + obj.get_id(), body=body, method='PUT')
