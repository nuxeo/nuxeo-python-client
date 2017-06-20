# coding: utf-8
from .common import NuxeoObject, NuxeoService


class DirectoryEntry(NuxeoObject):
    """
    Representation of an entry in a directory
    """
    entity_type = 'directoryEntry'

    def __init__(self, obj=None, service=None):
        super(DirectoryEntry, self).__init__(obj, service)
        self._entity_type = 'directoryEntry'
        self.directoryName = obj['directoryName']

    def get_id(self):
        return self.properties['id']


class Directory(NuxeoService):
    """
    Directory service allow you to modify a Directory on the server
    """
    def __init__(self, name, nuxeo):
        super(Directory, self).__init__(nuxeo, 'group', DirectoryEntry)
        self._name = name
        self._path = 'directory/' + name

    def fetchAll(self):
        """
        :return: all entries from the Directory
        """
        result = self._nuxeo.request(self._path)
        entries = []
        for entry in result['entries']:
            entries.append(DirectoryEntry(entry, self))
        return entries

    def create(self, obj):
        """
        Create a new entry in the directory

        :param obj: a object with properties attribute or a dict
        :return: The new created entry
        """
        if isinstance(obj, self._object_class):
            properties = obj.properties
        elif isinstance(obj, dict):
            properties = obj
        else:
            raise Exception("Need a dictionary of properties or a " + self._object_class + " object")
        return self._object_class(self._nuxeo.request(self._path, method='POST', body={'entity-type': self._object_class.entity_type, 'directoryName': self._name, 'properties': properties}), self)

    def update(self, obj):
        """
        Update an entry in the directory

        :param obj:
        """
        self._nuxeo.request(self._path + '/' + obj.get_id(), body={'entity-type': self._object_class.entity_type, 'properties': obj.properties, 'directoryName': self._name}, method='PUT')