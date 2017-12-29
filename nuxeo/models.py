# coding: utf-8
from __future__ import unicode_literals

import atexit
import os
from io import StringIO

from nuxeo.compat import text
from nuxeo.exceptions import InvalidBatch
from nuxeo.utils import guess_mimetype


class Model(object):
    _valid_properties = {}

    def __init__(self, service=None, **kwargs):
        self.service = service

    def as_dict(self):
        """ Returns a dict representation of the resource. """
        types = (int, float, str, list, dict, bytes, text)
        result = {}
        for key in self._valid_properties:
            val = getattr(self, key.replace('-', '_'))
            if not val:
                continue
            # Parse custom classes
            if not isinstance(val, types):
                val = val.as_dict()
            # Parse lists of objects
            elif isinstance(val, list) and not isinstance(val[0], types):
                val = [item.as_dict() for item in val]

            result[key] = val
        return result

    @classmethod
    def parse(cls, json, service=None):
        """ Parse a JSON object into a model instance. """
        model = cls()

        if service:
            setattr(model, 'service', service)

        for key, val in json.items():
            if key in cls._valid_properties:
                key = key.replace('-', '_')
                setattr(model, key, val)
        return model

    def save(self):
        self.service.put(self)


class Refreshable(object):
    _valid_properties = {}
    service = None
    id = None

    def load(self, model=None):
        # type: (Optional[Model]) -> None
        if not model:
            model = self.service.get(self.id)
        for key in self._valid_properties:
            key = key.replace('-', '_')
            setattr(self, key, getattr(model, key))


class Document(Model, Refreshable):
    _valid_properties = {
        'entity-type': 'document',
        'repository': 'default',
        'name': None,
        'uid': None,
        'path': None,
        'type': None,
        'state': None,
        'parentRef': None,
        'versionLabel': None,
        'isCheckedOut': False,
        'isVersion': False,
        'isProxy': False,
        'title': None,
        'lastModified': None,
        'properties': {},
        'facets': [],
        'changeToken': None,
        'contextParameters': {},
    }

    def __init__(self, **kwargs):
        super(Document, self).__init__(**kwargs)
        for key, default in Document._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def id(self):
        return self.uid

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
        """ Delete the document. """
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
        # type: (Text) -> Blob
        """
        Retrieve one of the blobs attached to the document.

        :param xpath: the xpath to the blob
        :return: the blob
        """
        return self.service.fetch_blob(uid=self.uid, xpath=xpath)

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
        self.load()

    def get(self, prop):
        # type: (Text) -> Any
        return self.properties[prop]

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
        :param name: Rename the document if specified
        """
        self.service.move(self.uid, dst, name)
        self.load()

    def remove_permission(self, params):
        # type: (Dict[Text, Any]) -> None
        """ Remove a permission to a document. """
        return self.service.remove_permission(self.uid, params)

    def set(self, properties):
        # type: (Dict[Text, Any]) -> None
        self.properties.update(properties)

    def start_workflow(self, model, options=None):
        # type: (Text, Optional[Dict[Text, Any]]) -> Workflow
        return self.service.start_workflow(self.uid, model, options=options)

    def unlock(self):
        # type: () -> Dict[Text, Any]
        """ Unlock the document. """
        return self.service.unlock(self.uid)


class Directory(Model):
    _valid_properties = {
        'entity-type': 'directory',
        'directoryName': None,
        'entries': []
    }

    def __init__(self, **kwargs):
        super(Directory, self).__init__(**kwargs)
        for key, default in Directory._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def id(self):
        return self.directoryName

    def get(self, entry=None):
        # type: (Optional[Text]) -> Union[DirectoryEntry, List[DirectoryEntry]]
        return self.service.get(self.id, dir_entry=entry)

    def create(self, entry):
        # type: (DirectoryEntry) -> DirectoryEntry
        return self.service.post(entry, dir_name=self.id)

    def save(self, entry):
        # type: (DirectoryEntry) -> DirectoryEntry
        return self.service.put(entry, dir_name=self.id)

    def delete(self, entry=None):
        # type: (Text) -> Union[Directory, DirectoryEntry]
        return self.service.delete(self.id, dir_entry=entry)

    def exists(self, entry):
        # type: (Text) -> bool
        return self.service.exists(self.id, dir_entry=entry)


class DirectoryEntry(Model):
    _valid_properties = {
        'entity-type': 'directoryEntry',
        'directoryName': None,
        'properties': {},
    }

    def __init__(self, **kwargs):
        super(DirectoryEntry, self).__init__(**kwargs)
        for key, default in DirectoryEntry._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def id(self):
        return self.properties['id']

    def save(self):
        # type: () -> DirectoryEntry
        return self.service.put(self, self.directoryName, self.id)

    def delete(self):
        # type: () -> DirectoryEntry
        return self.service.delete(self.directoryName, self.id)


class Group(Model):
    _valid_properties = {
        'entity-type': 'group',
        'groupname': None,
        'grouplabel': None,
        'memberUsers': [],
        'memberGroups': [],
    }

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        for key, default in Group._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def id(self):
        return self.groupname

    def delete(self):
        # type: () -> Group
        return self.service.delete(self.id)


class User(Model, Refreshable):
    _valid_properties = {
        'entity-type': 'user',
        'id': None,
        'properties': {},
        'extendedGroups': [],
        'isAdministrator': False,
        'isAnonymous': False,
    }

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        for key, default in User._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    def change_password(self, password):
        # type: (Text) -> None
        """
        Change user password.

        :param password: New password to set
        """
        self.properties['password'] = password
        self.save()

    def delete(self):
        self.service.delete(self.id)


class Workflow(Model):
    _valid_properties = {
        'entity-type': 'workflow',
        'id': None,
        'name': None,
        'title': None,
        'state': None,
        'workflowModelName': None,
        'initiator': None,
        'attachedDocumentIds': [],
        'variables': {},
        'graphResource': None,
    }

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        for key, default in Workflow._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    def delete(self):
        self.service.delete(self.id)

    def graph(self):
        return self.service.graph(self)

    def tasks(self):
        return self.service.tasks(self)


class Task(Model, Refreshable):
    _valid_properties = {
        'entity-type': 'task',
        'id': None,
        'name': None,
        'workflowInstanceId': None,
        'workflowModelName': None,
        'state': None,
        'directive': None,
        'created': None,
        'dueDate': None,
        'nodeName': None,
        'targetDocumentIds': [],
        'actors': [],
        'comments': [],
        'variables': {},
        'taskInfo': {},
    }

    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)
        for key, default in Task._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    def complete(self, action, variables=None, comment=None):
        # type: (Text, Optional[Dict[Text, Any]], Optional[Text]) -> None
        updated_task = self.service.complete(
            self, action, variables=variables, comment=comment)
        self.load(updated_task)

    def delegate(self, actors, comment=None):
        # type: (Text, Optional[Text]) -> None
        """ Delegate the Task to someone else. """
        self.service.transfer(self, 'delegate', actors, comment=comment)
        self.load()

    def reassign(self, actors, comment=None):
        # type: (Text, Optional[Text]) -> None
        """ Reassign the Task to someone else. """
        self.service.transfer(self, 'reassign', actors, comment=comment)
        self.load()


class Batch(Model):
    _valid_properties = {
        'batchId': None,
        'dropped': None,
    }

    def __init__(self, **kwargs):
        super(Batch, self).__init__(**kwargs)
        self.blobs = {}
        self.batchId = None
        self.upload_idx = 0
        for key, default in Batch._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    @property
    def id(self):
        return self.batchId

    @id.setter
    def id(self, value):
        self.batchId = value

    def get(self, file_idx):
        # type: (int) -> Blob
        if self.batchId is None:
            raise InvalidBatch('Cannot fetch blob for inexistant/deleted batch.')
        blob = self.service.get(self.id, file_idx=file_idx)
        self.blobs[file_idx] = blob
        return blob

    def cancel(self):
        # type: () -> None
        if not self.batchId:
            return
        self.service.delete(self.id)
        self.batchId = None

    def upload(self, blob):
        # type: (Blob) -> Blob
        return self.service.upload(self, blob)


class Blob(Model):
    _valid_properties = {
        'uploaded': 'true',
        'name': None,
        'uploadType': None,
        'size': 0,
        'uploadedSize': None,
        'fileIdx': None,
        'mimetype': None,
    }

    def __init__(self, **kwargs):
        super(Blob, self).__init__(**kwargs)
        for key, default in Blob._valid_properties.items():
            if key == 'uploaded':
                val = kwargs.get(key, 'true') == 'true'
            elif key == 'size':
                val = kwargs.get(key, 0)
            elif key == 'uploadedSize':
                val = kwargs.get(key, kwargs.get('size', 0))
            else:
                val = kwargs.get(key, default)
            setattr(self, key, val)

    @classmethod
    def parse(cls, json, service=None):
        """ Parse a JSON object into a model instance. """
        model = cls()

        if service:
            setattr(model, 'service', service)

        for key, val in json.items():
            if key in cls._valid_properties:
                setattr(model, key, val)

        if model.uploaded and model.uploadedSize == 0:
            model.uploadedSize = model.size
        return model

    def to_json(self):
        # type: () -> Dict[Text, Text]
        return {
            'upload-batch': self.batch_id,
            'upload-fileId': text(self.fileIdx),
        }


class BufferBlob(Blob):
    """ InMemory content to upload to Nuxeo. """

    def __init__(self, data, **kwargs):
        # type: (Text, **Any) -> None
        """
        :param data: content to upload to Nuxeo
        :param **kwargs: named attributes
        """
        super(BufferBlob, self).__init__(**kwargs)
        self.buffer = data
        self.mimetype = self.mimetype or 'application/octet-stream'

    @property
    def data(self):
        # type: () -> StringIO
        """ Request data. """
        return StringIO(self.buffer)


class FileBlob(Blob):
    """ Represent a File as Blob for future upload. """

    # File descriptor
    fd = None  # type: Optional[IO[bytes]]

    def __init__(self, path, **kwargs):
        # type: (Text, **Any) -> None
        """
        :param path: file path
        :param **kwargs: named attributes
        """
        super(FileBlob, self).__init__(**kwargs)
        self.path = path
        self.name = os.path.basename(self.path)
        self.size = os.path.getsize(self.path)
        self.mimetype = self.mimetype or guess_mimetype(self.path)
        atexit.register(self.on_exit)

    def on_exit(self):
        # type: () -> None
        """ Ensure the file descriptor is closed on exit. """

        if self.fd:
            self.fd.close()
            self.fd = None

    @property
    def data(self):
        # type: () -> IO[bytes]
        """
        Request data.

        The caller is not required to manually close the file descriptor.
        It will be done when the class object is destroyed.
        """

        self.fd = open(self.path, 'rb')
        return self.fd


class Operation(Model):
    _valid_properties = {
        'command': None,
        'input_obj': None,
        'params': {},
        'progress': 0,
    }

    def __init__(self, **kwargs):
        super(Operation, self).__init__(**kwargs)
        for key, default in Operation._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    def execute(self, **kwargs):
        return self.service.execute(self, **kwargs)
