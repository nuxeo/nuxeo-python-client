# coding: utf-8
from __future__ import unicode_literals

from .common import NuxeoObject, NuxeoService

__all__ = ('Directory', 'DirectoryEntry')


class DirectoryEntry(NuxeoObject):
    """ Representation of an entry in a directory. """

    entity_type = 'directoryEntry'

    def __init__(self, obj=None, service=None):
        super(DirectoryEntry, self).__init__(obj, service)
        self._entity_type = 'directoryEntry'
        self.directoryName = obj['directoryName']

    def get_id(self):
        return self.properties['id']


class Directory(NuxeoService):
    """ Directory service allow you to modify a Directory on the server. """

    def __init__(self, name, nuxeo):
        super(Directory, self).__init__(nuxeo, 'group', DirectoryEntry)
        self._name = name
        self._path = 'directory/' + name

    def fetchAll(self):
        """
        :return: all entries from the Directory
        """
        result = self._nuxeo.request(self._path)
        return [DirectoryEntry(entry, self) for entry in result['entries']]

    def create(self, obj):
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

    def update(self, obj):
        """ Update an entry in the directory. """

        body = {
            'entity-type': self._object_class.entity_type,
            'properties': obj.properties,
            'directoryName': self._name,
        }
        self._nuxeo.request(
            self._path + '/' + obj.get_id(), body=body, method='PUT')
