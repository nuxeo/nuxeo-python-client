__author__ = 'loopingz'

from common import NuxeoAutosetObject


class Document(NuxeoAutosetObject):

    def __init__(self, obj=None, service=None):
        super(Document, self).__init__(obj=obj, service=service)
        self.path = obj['path']
        self.uid = obj['uid']
        self.facets = obj['facets']
        self.repository = obj['repository']
        self.title = obj['title']
        self.lastModified = obj['lastModified']
        self.state = obj['state']
        self.isCheckedOut = obj['isCheckedOut']
        self.parentRef = obj['parentRef']
        self.type = obj['type']
        self.changeToken = obj['changeToken']

    def get_id(self):
        return self.uid

    def set(self, properties):
        for key in properties:
            self.properties[key] = properties[key]