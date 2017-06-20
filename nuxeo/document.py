# coding: utf-8
from .common import NuxeoAutosetObject


class Document(NuxeoAutosetObject):
    """
    Represent a Document on the Nuxeo Server
    """
    def __init__(self, obj=None, service=None):
        super(Document, self).__init__(obj=obj, service=service)
        self._read(obj)

    def _read(self, obj):
        self.path = obj['path']
        self.uid = obj['uid']
        self.facets = obj['facets']
        self.repository = obj['repository']
        self.title = obj['title']
        try:
            self.lastModified = obj['lastModified']
        except KeyError:
            self.lastModified = None
        self.state = obj['state']
        self.isCheckedOut = obj['isCheckedOut']
        self.parentRef = obj['parentRef']
        self.type = obj['type']
        self.changeToken = obj['changeToken']

    def fetch_renditions(self):
        """

        :return: Available renditions for this document
        """
        return self._service.fetch_renditions(self.get_id())

    def fetch_rendition(self, name):
        """

        :param name: Rendition name to use
        :return: The rendition content
        """
        return self._service.fetch_rendition(self.get_id(), name)

    def get_id(self):
        return self.uid

    def delete(self):
        """
        Delete the current Document
        """
        self._service.delete(self.get_id())

    def refresh(self):
        """
        Refresh the Document with last informations from the server
        """
        self._read(self._service.get(self.get_id()))

    def convert(self, params):
        """
        Convert the document to another format

        :param params: Converter permission
        :return: the converter result
        """
        return self._service.convert(self.get_id(), params)

    def lock(self):
        """
        Lock the document
        """
        return self._service.lock(self.get_id())

    def unlock(self):
        """
        Unlock the document
        """
        return self._service.unlock(self.get_id())

    def fetch_lock_status(self):
        """
        Get lock status
        """
        return self._service.fetch_lock_status(self.get_id())

    def fetch_acls(self):
        """
        Fetch document ACLs
        """
        return self._service.fetch_acls(self.get_id())

    def add_permission(self, params):
        """
        Add a permission to a document

        :param params: permission to add
        """
        return self._service.add_permission(self.get_id(), params)

    def remove_permission(self, params):
        """
        Remove a permission to a document
        """
        return self._service.remove_permission(self.get_id(), params)

    def has_permission(self, params):
        """
        Verify if a document has the permission
        """
        return self._service.has_permission(self.get_id(), params)

    def fetch_blob(self, xpath='blobholder:0'):
        """
        Get Document blob content

        :param xpath: by default first blob attached you can set the xpath to blobholder:1 for second blob and so on
        """
        return self._service.fetch_blob(self.get_id(), xpath)

    def set(self, properties):
        for key in properties:
            self.properties[key] = properties[key]

    def move(self, dst, name = None):
        """
        Move a document into another parent

        :param dst: The new parent path
        :param name: New name if specified, normal move otherwise
        """
        self._service.move(self.get_id(), dst, name)
        self.refresh()

    def follow_transition(self, name):
        """
        Follow a lifecycle transition on this document

        :param name: transition name
        """
        self._service.follow_transition(self.get_id(), name)
        self.refresh()

    def fetch_audit(self):
        """
        Fetch audit for current document

        """
        return self._service.fetch_audit(self.get_id())

    def fetch_workflows(self):
        """
        Fetch the workflows running on this document
        """
        return self._service.fetch_workflows(self.get_id())

    def start_workflow(self, name, options=dict()):
        """
        Start a workflow on a document

        :param name: Workflow name
        :param options: Workflow options
        :return: the Workflow object
        """
        return self._service.start_workflow(name, self.get_id(), options)
