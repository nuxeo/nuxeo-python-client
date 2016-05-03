__author__ = 'loopingz'

from common import NuxeoAutosetObject


class Document(NuxeoAutosetObject):

    def __init__(self, obj=None, service=None):
        super(Document, self).__init__(obj=obj, service=service)
        self._read(obj)

    def _read(self, obj):
        self.path = obj['path']
        self.uid = obj['uid']
        self.facets = obj['facets']
        self.repository = obj['repository']
        self.title = obj['title']
        if 'lastModified' in obj:
            self.lastModified = obj['lastModified']
        else:
            self.lastModified = None
        self.state = obj['state']
        self.isCheckedOut = obj['isCheckedOut']
        self.parentRef = obj['parentRef']
        self.type = obj['type']
        self.changeToken = obj['changeToken']

    def fetch_renditions(self):
        return self._service.fetch_renditions(self.get_id())

    def fetch_rendition(self, name):
        return self._service.fetch_rendition(self.get_id(), name)

    def get_id(self):
        return self.uid

    def refresh(self):
        self._read(self._service.get(self.get_id()))

    def convert(self, params):
        return self._service.convert(self.get_id(), params)

    def fetch_acls(self):
        return self._service.fetch_acls(self.get_id())

    def add_permission(self, params):
        return self._service.add_permission(self.get_id(), params)

    def remove_permission(self, params):
        return self._service.remove_permission(self.get_id(), params)

    def fetch_blob(self, xpath='blobholder:0'):
        return self._service.fetch_blob(self.get_id(), xpath)

    def set(self, properties):
        for key in properties:
            self.properties[key] = properties[key]