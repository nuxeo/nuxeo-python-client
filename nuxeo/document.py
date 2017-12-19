# coding: utf-8
from __future__ import unicode_literals

from typing import Any, Dict, Optional, Text, Union

from .common import NuxeoAutosetObject

__all__ = ('Document',)


class Document(NuxeoAutosetObject):
    """ Represent a Document on the Nuxeo Server. """

    def __init__(self, obj, service):
        # type: (Dict[Text, Any], Repository) -> None
        super(Document, self).__init__(obj=obj, service=service)
        self._read(obj)

    def add_permission(self, params):
        # type: (Dict[Text, Any]) -> None
        """ Add a permission to a document.

        :param params: permission to add
        """
        return self.service.add_permission(self.uid, params)

    def convert(self, params):
        # type: (Dict[Text, Any]) -> Union[Dict[Text, Any], Text]
        """
        Convert the document to another format.

        :param params: Converter permission
        :return: the converter result
        """
        return self.service.convert(self.uid, params)

    def delete(self):
        # type: () -> None
        """ Delete the current Document. """
        self.service.delete(self.uid)

    def fetch_acls(self):
        # type: () -> Dict[Text, Any]
        """ Fetch document ACLs. """
        return self.service.fetch_acls(self.uid)

    def fetch_audit(self):
        # type: () -> Dict[Text, Any]
        """ Fetch audit for current document. """
        return self.service.fetch_audit(self.uid)

    def fetch_blob(self, xpath='blobholder:0'):
        # type: (Text) -> Union[Dict[Text, Any], Text, bytes]
        """
        Get Document blob content.

        :param xpath: by default first blob attached.  You can set the xpath
                      to blobholder:1 for second blob, and so on.
        """
        return self.service.fetch_blob(self.uid, xpath)

    def fetch_lock_status(self):
        # type: () -> Dict[Text, Any]
        """ Get lock informations. """
        return self.service.fetch_lock_status(self.uid)

    def fetch_rendition(self, name):
        # type: (Text) -> Dict[Text, Any]
        """
        :param name: Rendition name to use
        :return: The rendition content
        """
        return self.service.fetch_rendition(self.uid, name)

    def fetch_renditions(self):
        # type: () -> list
        """
        :return: Available renditions for this document
        """
        return self.service.fetch_renditions(self.uid)

    def fetch_workflows(self):
        # type: () -> list
        """ Fetch the workflows running on this document. """
        return self.service.fetch_workflows(self.uid)

    def follow_transition(self, name):
        # type: (Text) -> None
        """
        Follow a lifecycle transition on this document.

        :param name: transition name
        """
        self.service.follow_transition(self.uid, name)
        self.refresh()

    def get_id(self):
        # type: () -> Text
        return self.uid

    def has_permission(self, params):
        # type: (Dict[Text, Any]) -> bool
        """ Verify if a document has the permission. """
        return self.service.has_permission(self.uid, params)

    def is_locked(self):
        # type: () -> bool
        """ Get lock status. """
        return not not self.fetch_lock_status()

    def lock(self):
        # type: () -> Dict[Text, Any]
        """ Lock the document. """
        return self.service.lock(self.uid)

    def move(self, dst, name=None):
        # type: (Text, Optional[Text]) -> None
        """
        Move a document into another parent.

        :param dst: The new parent path
        :param name: New name if specified, normal move otherwise
        """
        self.service.move(self.uid, dst, name)
        self.refresh()

    def refresh(self):
        # type: () -> None
        """ Refresh the Document with last informations from the server. """
        self._read(self.service.get(self.uid))

    def remove_permission(self, params):
        # type: (Dict[Text, Any]) -> None
        """ Remove a permission to a document. """
        return self.service.remove_permission(self.uid, params)

    def set(self, properties):
        # type: (Dict[Text, Any]) -> None
        self.properties.update(properties)

    def start_workflow(self, name, options=None):
        # type: (Text, Optional[Dict[Text, Any]]) -> Workflow
        """
        Start a workflow on a document.

        :param name: Workflow name
        :param options: Workflow options
        :return: the Workflow object
        """
        return self.service.start_workflow(name, self.uid, options or {})

    def unlock(self):
        # type: () -> Dict[Text, Any]
        """ Unlock the document. """
        return self.service.unlock(self.uid)

    def _read(self, obj):
        # type: (Dict[Text, Any]) -> None
        self.path = obj['path']
        self.uid = obj['uid']
        self.facets = obj['facets']
        self.repository = obj['repository']
        self.title = obj['title']
        self.lastModified = obj.get('lastModified')
        self.state = obj['state']
        self.isCheckedOut = obj['isCheckedOut']
        self.parentRef = obj['parentRef']
        self.type = obj['type']
        self.changeToken = obj['changeToken']
