# coding: utf-8
from __future__ import unicode_literals

import os
from io import StringIO

from .compat import text
from .exceptions import InvalidBatch
from .utils import guess_mimetype

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, BinaryIO, Dict, List, Optional, Text, Union  # noqa
        from io import FileIO  # noqa
        from .directories import API as DirectoriesAPI  # noqa
        from .documents import API as DocumentsAPI  # noqa
        from .endpoint import APIEndpoint  # noqa
        from .groups import API as GroupsAPI  # noqa
        from .operations import API as OperationsAPI  # noqa
        from .tasks import API as TasksAPI  # noqa
        from .uploads import API as UploadsAPI  # noqa
        from .users import API as UsersAPI  # noqa
        from .workflows import API as WorkflowsAPI  # noqa
except ImportError:
    pass

""" Base classes """


class Model(object):
    """ Base class for all entities. """
    _valid_properties = {}  # type: Dict[Text, Any]
    service = None  # type: APIEndpoint
    uid = None  # type: Text

    def __init__(self, service=None, **kwargs):
        # type: (Optional[APIEndpoint], Any) -> None
        self.service = service

    def __repr__(self):
        # type: () -> Text
        attrs = ', '.join('{}={!r}'.format(
            attr, getattr(self, attr.replace('-', '_'), None))
            for attr in sorted(self._valid_properties))
        return '<{} {}>'.format(self.__class__.__name__, attrs)

    def as_dict(self):
        # type: () -> Dict[Text, Any]
        """ Returns a dict representation of the resource. """
        result = {}
        for key in self._valid_properties:
            val = getattr(self, key.replace('-', '_'))
            if val is None:
                continue
            # Parse lists of objects
            elif (isinstance(val, list) and len(val) > 0
                  and isinstance(val[0], Model)):
                val = [item.as_dict() for item in val]

            result[key] = val
        return result

    @classmethod
    def parse(cls, json, service=None):
        # type: (Dict[Text, Any], Optional[APIEndpoint]) -> Model
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
        # type: () -> None
        """ Save the resource. """
        self.service.put(self)


class RefreshableModel(Model):

    def load(self, model=None):
        # type: (Optional[Union[Model, Dict[Text, Any]]]) -> None
        """
        Reload the Model.

        If model is not None, copy from its attributes,
        otherwise query the server for the entity with its uid.

        :param model: the entity to copy
        :return: the refreshed model
        """
        if not model:
            model = self.service.get(self.uid)

        if isinstance(model, dict):
            def get_prop(obj, key):
                return obj.get(key)
        else:
            def get_prop(obj, key):
                return getattr(obj, key)

        for key in self._valid_properties:
            key = key.replace('-', '_')
            setattr(self, key, get_prop(model, key))


""" Entities """


class Batch(Model):
    """ Upload batch. """

    _valid_properties = {
        'batchId': None,
        'dropped': None,
    }
    service = None  # type: UploadsAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Batch, self).__init__(**kwargs)
        self.batchId = None  # type: Text
        self.blobs = {}  # type: Dict[int, Blob]
        self._upload_idx = 0
        for key, default in Batch._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    @property
    def uid(self):
        # type: () -> Text
        return self.batchId

    @uid.setter
    def uid(self, value):
        # type: (Text) -> None
        self.batchId = value

    def cancel(self):
        # type: () -> None
        """ Cancel an upload batch. """
        if not self.batchId:
            return
        self.service.delete(self.uid)
        self.batchId = None

    def delete(self, file_idx):
        """ Delete a blob from the batch. """
        if self.batchId:
            self.service.delete(self.uid, file_idx=file_idx)
            self.blobs[file_idx] = None

    def get(self, file_idx):
        # type: (int) -> Blob
        """
        Get the blob info.

        :param file_idx: the index of the blob in the batch
        :return: the corresponding blob
        """
        if self.batchId is None:
            raise InvalidBatch(
                'Cannot fetch blob for inexistant/deleted batch.')
        blob = self.service.get(self.uid, file_idx=file_idx)
        self.blobs[file_idx] = blob
        return blob

    def get_uploader(self, blob, **kwargs):
        # type: (Blob, Any) -> Blob
        """
        Get an uploader for blob.

        :param blob: the blob to upload
        :param kwargs: the upload settings
        :return: the uploader
        """
        return self.service.get_uploader(self, blob, **kwargs)

    def upload(self, blob, **kwargs):
        # type: (Blob, Any) -> Blob
        """
        Upload a blob.

        :param blob: the blob to upload
        :param kwargs: the upload settings
        :return: the blob info
        """
        return self.service.upload(self, blob, **kwargs)

    def execute(self, operation, file_idx=None, params=None):
        # type: (Text, int, Dict[Text, Any]) -> Any
        """
        Execute an operation on this batch.

        :param operation: operation to execute
        :param file_idx: target file of the operation
        :param params: parameters of the operation
        :return: the output of the operation
        """
        return self.service.execute(self, operation, file_idx, params)

    def attach(self, doc, file_idx=None):
        # type: (Text, Optional[int]) -> Any
        """
        Attach one or all files of this batch to a document.

        :param doc: document to attach
        :param file_idx: target file
        :return: the output of the attach operation
        """
        return self.service.attach(self, doc, file_idx)


class Blob(Model):
    """ Blob superclass used for metadata. """

    _valid_properties = {
        'uploaded': 'true',
        'name': None,
        'uploadType': None,
        'size': 0,
        'uploadedSize': 0,
        'fileIdx': None,
        'mimetype': None,
        'uploadedChunkIds': [],
        'chunkCount': 0
    }
    service = None  # type: UploadsAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
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
        # type: (Dict[Text, Any], Optional[APIEndpoint]) -> Blob
        """ Parse a JSON object into a blob instance. """
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
        """ Return a JSON object used during the upload. """
        return {
            'upload-batch': self.batch_id,
            'upload-fileId': text(self.fileIdx),
        }


class BufferBlob(Blob):
    """
    InMemory content to upload to Nuxeo.

    Acts as a context manager so its data can be read
    with the `with` statement.
    """

    stringio = None  # type: Optional[StringIO]

    def __init__(self, data, **kwargs):
        # type: (Text, Any) -> None
        """
        :param data: content to upload to Nuxeo
        :param **kwargs: named attributes
        """
        super(BufferBlob, self).__init__(**kwargs)
        self.buffer = data
        self.size = len(self.buffer)
        self.mimetype = 'application/octet-stream'

    @property
    def data(self):
        # type: () -> StringIO
        """ Request data. """
        return self.stringio

    def __enter__(self):
        if not self.buffer:
            return None
        self.stringio = StringIO(self.buffer)
        return self.stringio

    def __exit__(self, *args):
        if self.stringio:
            self.stringio.close()


class FileBlob(Blob):
    """
    File to upload to Nuxeo.

    Acts as a context manager so its data can be read
    with the `with` statement.
    """

    # File descriptor
    fd = None  # type: Optional[BinaryIO]

    def __init__(self, path, **kwargs):
        # type: (Text, Any) -> None
        """
        :param path: file path
        :param **kwargs: named attributes
        """
        super(FileBlob, self).__init__(**kwargs)
        self.path = path
        self.name = os.path.basename(self.path)
        self.size = os.path.getsize(self.path)
        self.mimetype = (self.mimetype
                         or guess_mimetype(self.path))  # type: Text

    @property
    def data(self):
        # type: () -> BinaryIO
        """
        Request data.

        The caller has to close the file descriptor
        himself if he doesn't open it with the
        context manager.
        """
        return self.fd

    def __enter__(self):
        self.fd = open(self.path, 'rb')
        return self.fd

    def __exit__(self, *args):
        if self.fd:
            self.fd.close()


class Directory(Model):
    """ Directory. """
    _valid_properties = {
        'entity-type': 'directory',
        'directoryName': None,
        'entries': []
    }
    service = None  # type: DirectoriesAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Directory, self).__init__(**kwargs)
        for key, default in Directory._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def uid(self):
        # type: () -> Text
        return self.directoryName

    def get(self, entry):
        # type: (Text) -> DirectoryEntry
        """
        Get an entry of the directory.

        :param entry: the name of the entry
        :return: the corresponding directory entry
        """
        return self.service.get(self.uid, dir_entry=entry)

    def create(self, entry):
        # type: (DirectoryEntry) -> DirectoryEntry
        """ Create an entry in the directory. """
        return self.service.post(entry, dir_name=self.uid)

    def save(self, entry):
        # type: (DirectoryEntry) -> DirectoryEntry
        """ Save a modified entry of the directory. """
        return self.service.put(entry, dir_name=self.uid)

    def delete(self, entry):
        # type: (Text) -> None
        """
        Delete one of the directory's entries.

        :param entry: the entry to delete
        """
        self.service.delete(self.uid, entry)

    def exists(self, entry):
        # type: (Text) -> bool
        """
        Check if an entry is in the directory.

        :param entry: the entry name
        :return: True if it exists, else False
        """
        return self.service.exists(self.uid, dir_entry=entry)


class DirectoryEntry(Model):
    """ Directory entry. """
    _valid_properties = {
        'entity-type': 'directoryEntry',
        'directoryName': None,
        'properties': {},
    }
    service = None  # type: DirectoriesAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(DirectoryEntry, self).__init__(**kwargs)
        for key, default in DirectoryEntry._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def uid(self):
        # type: () -> Text
        return self.properties['id']

    def save(self):
        # type: () -> DirectoryEntry
        """ Save the entry. """
        return self.service.put(self, self.directoryName)

    def delete(self):
        # type: () -> None
        """ Delete the entry. """
        self.service.delete(self.directoryName, self.uid)


class Document(RefreshableModel):
    """ Document. """
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
        'isTrashed': False,
        'isVersion': False,
        'isProxy': False,
        'title': None,
        'lastModified': None,
        'properties': {},
        'facets': [],
        'changeToken': None,
        'contextParameters': {},
    }
    service = None  # type: DocumentsAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Document, self).__init__(**kwargs)
        for key, default in Document._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def workflows(self):
        # type: () -> List[Workflow]
        """ Return the workflows associated with the document. """
        return self.service.workflows(self)

    def add_permission(self, params):
        # type: (Dict[Text, Any]) -> None
        """
        Add a permission to a document.

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
        # type: (Text) -> Union[Text, bytes]
        """
        :param name: Rendition name to use
        :return: The rendition content
        """
        return self.service.fetch_rendition(self.uid, name)

    def fetch_renditions(self):
        # type: () -> List[Union[Text, bytes]]
        """
        :return: Available renditions for this document
        """
        return self.service.fetch_renditions(self.uid)

    def follow_transition(self, name):
        # type: (Text) -> None
        """
        Follow a lifecycle transition on this document.

        :param name: transition name
        """
        doc = self.service.follow_transition(self.uid, name)
        self.load(doc)

    def get(self, prop):
        # type: (Text) -> Any
        """ Get a property of the document by its name. """
        return self.properties[prop]

    def has_permission(self, permission):
        # type: (Text) -> bool
        """ Verify if a document has the permission. """
        return self.service.has_permission(self.uid, permission)

    def is_locked(self):
        # type: () -> bool
        """ Get the lock status. """
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
        doc = self.service.move(self.uid, dst, name)
        self.load(doc)

    def remove_permission(self, params):
        # type: (Dict[Text, Any]) -> None
        """ Remove a permission to a document. """
        return self.service.remove_permission(self.uid, params)

    def set(self, properties):
        # type: (Dict[Text, Any]) -> None
        """ Add/update the properties of the document. """
        self.properties.update(properties)

    def trash(self):
        # type: () -> None
        doc = self.service.trash(self.uid)
        self.load(doc)

    def unlock(self):
        # type: () -> Dict[Text, Any]
        """ Unlock the document. """
        return self.service.unlock(self.uid)

    def untrash(self):
        # type: () -> None
        doc = self.service.untrash(self.uid)
        self.load(doc)


class Group(Model):
    """ User group. """
    _valid_properties = {
        'entity-type': 'group',
        'groupname': None,
        'grouplabel': None,
        'memberUsers': [],
        'memberGroups': [],
    }
    service = None  # type: GroupsAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Group, self).__init__(**kwargs)
        for key, default in Group._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def uid(self):
        # type: () -> Text
        return self.groupname

    def delete(self):
        # type: () -> None
        """ Delete the group. """
        self.service.delete(self.uid)


class Operation(Model):
    """ Automation operation. """
    _valid_properties = {
        'command': None,
        'input_obj': None,
        'params': {},
        'context': None,
        'progress': 0,
    }
    service = None  # type: OperationsAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Operation, self).__init__(**kwargs)
        for key, default in Operation._valid_properties.items():
            setattr(self, key, kwargs.get(key, default))

    def execute(self, **kwargs):
        # type: (Any) -> Any
        """ Execute the operation. """
        return self.service.execute(self, **kwargs)


class Task(RefreshableModel):
    """ Workflow task. """
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
    service = None  # type: TasksAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Task, self).__init__(**kwargs)
        for key, default in Task._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def uid(self):
        # type: () -> Text
        return self.id

    def complete(self, action, variables=None, comment=None):
        # type: (Text, Optional[Dict[Text, Any]], Optional[Text]) -> None
        """ Complete the action of a task. """
        updated_task = self.service.complete(
            self, action, variables=variables, comment=comment)
        self.load(updated_task)

    def delegate(self, actors, comment=None):
        # type: (Text, Optional[Text]) -> None
        """ Delegate the task to someone else. """
        self.service.transfer(self, 'delegate', actors, comment=comment)
        self.load()

    def reassign(self, actors, comment=None):
        # type: (Text, Optional[Text]) -> None
        """ Reassign the task to someone else. """
        self.service.transfer(self, 'reassign', actors, comment=comment)
        self.load()


class User(RefreshableModel):
    """ User. """
    _valid_properties = {
        'entity-type': 'user',
        'id': None,
        'properties': {},
        'extendedGroups': [],
        'isAdministrator': False,
        'isAnonymous': False,
    }
    service = None  # type: UsersAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(User, self).__init__(**kwargs)
        for key, default in User._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def uid(self):
        # type: () -> Text
        return self.id

    def change_password(self, password):
        # type: (Text) -> None
        """
        Change user password.

        :param password: New password to set
        """
        self.properties['password'] = password
        self.save()

    def delete(self):
        # type: () -> None
        """ Delete the user. """
        self.service.delete(self.uid)


class Workflow(Model):
    """ Workflow. """
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
    service = None  # type: WorkflowsAPI

    def __init__(self, **kwargs):
        # type: (Any) -> None
        super(Workflow, self).__init__(**kwargs)
        for key, default in Workflow._valid_properties.items():
            key = key.replace('-', '_')
            setattr(self, key, kwargs.get(key, default))

    @property
    def tasks(self):
        # type: () -> List[Task]
        """ Return the tasks associated with the workflow. """
        return self.service.tasks(self)

    @property
    def uid(self):
        # type: () -> Text
        return self.id

    def delete(self):
        # type: () -> None
        """ Delete the workflow. """
        self.service.delete(self.uid)

    def graph(self):
        # type: () -> Dict[Text, Any]
        """ Return a JSON representation of the workflow graph. """
        return self.service.graph(self)
