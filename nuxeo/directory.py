__author__ = 'loopingz'
from common import NuxeoObject
from common import NuxeoService


class DirectoryEntry(NuxeoObject):

    entity_type = 'directoryEntry'

    def __init__(self, obj=None, service=None):
        super(DirectoryEntry, self).__init__(obj, service)
        self._entity_type = 'directoryEntry'
        self.directoryName = obj['directoryName']


class Directory(NuxeoService):
    """
    Users management
    """
    def __init__(self, name, nuxeo):
        super(Directory, self).__init__(nuxeo, 'group', DirectoryEntry)
        self._name = name
        self._path = 'directory/' + name

    def fetchAll(self):
        result = self._nuxeo.request(self._path)
        entries = []
        for entry in result['entries']:
            entries.append(DirectoryEntry(entry, self))
        return entries

    def create(self, obj):
        if isinstance(obj, self._object_class):
            properties = obj.properties
        elif isinstance(obj, dict):
            properties = obj
        else:
            raise Exception("Need a dictionary of properties or a " + self._object_class + " object")
        return self._object_class(self._nuxeo.request(self._path, method='POST', body={'entity-type': self._object_class.entity_type, 'directoryName': self._name, 'properties': properties}), self)

    def update(self, obj):
        self._nuxeo.request(self._path + '/' + obj.get_id(), body={'entity-type': self._object_class.entity_type, 'properties': obj.properties, 'directoryName': self._name}, method='PUT')