# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .exceptions import BadQuery, HTTPError, UnavailableConvertor
from .models import Document
from .utils import SwapAttr
from .workflows import API as WorkflowsAPI

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text, Union  # noqa
        from .client import NuxeoClient  # noqa
        from .models import Blob, Workflow  # noqa
        from .operations import API as OperationsAPI  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for documents. """
    def __init__(
        self,
        client,  # type: NuxeoClient
        operations,  # type: OperationsAPI
        workflows,  # type: WorkflowsAPI
        endpoint=None,  # type: Text
        headers=None,  # type: Optional[Dict[Text, Text]]
    ):
        # type: (...) -> None
        self.operations = operations
        self.workflows_api = workflows
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Document, headers=headers)

    def get(self, uid=None, path=None):
        # type: (Optional[Text], Optional[Text]) -> Document
        """
        Get the detail of a document.

        :param uid: the uid of the document
        :param path: the path of the document
        :return: the document
        """
        return super(API, self).get(path=self._path(uid=uid, path=path))

    def post(self, document, parent_id=None, parent_path=None):
        # type: (Document, Optional[Text], Optional[Text]) -> Document
        """
        Create a document.

        :param document: the document to create
        :param parent_id: the id of the parent document
        :param parent_path: the path of the parent document
        :return: the created document
        """
        return super(API, self).post(
            document, path=self._path(uid=parent_id, path=parent_path))

    create = post  # Alias for clarity

    def put(self, document):
        # type: (Document) -> Document
        """
        Update a document.

        :param document: the document to update
        :return: the updated document
        """
        return super(API, self).put(
            document, path=self._path(uid=document.uid))

    def delete(self, document_id):
        # type: (Text) -> None
        """
        Delete a document.

        :param document_id: the id of the document to delete
        """
        super(API, self).delete(self._path(uid=document_id))

    def exists(self, uid=None, path=None):
        # type: (Optional[Text], Optional[Text]) -> bool
        """
        Check if a document exists.

        :param uid: the id of the document to check
        :param path: the path of the document to check
        :return: True if it exists, else False
        """
        try:
            self.get(uid=uid, path=path)
            return True
        except HTTPError as e:
            if e.status != 404:
                raise e
        return False

    def add_permission(self, uid, params):
        # type: (Text, Dict[Text, Any]) -> None
        """
        Add a permission to a document.

        :param uid: the uid of the document
        :param params: the permissions to add
        """
        self.operations.execute(
            command='Document.AddPermission', input_obj=uid, params=params)

    def convert(self, uid, options):
        # type: (Text, Dict[Text, Text]) -> Union[Text, Dict[Text, Any]]
        """
        Convert a blob into another format.

        :param uid: the uid of the blob to be converted
        :param options: the target type, target format,
                        or converter for the blob
        :return: the response from the server
        """
        xpath = options.pop('xpath', 'blobholder:0')
        adapter = 'blob/{}/@convert'.format(xpath)
        if ('converter' not in options
                and 'type' not in options
                and'format' not in options):
            raise BadQuery(
                'One of (converter, type, format) is mandatory in options')

        try:
            return super(API, self).get(
                path=self._path(uid=uid), params=options,
                adapter=adapter, raw=True)
        except HTTPError as e:
            if 'is not registered' in e.message:
                raise BadQuery(e.message)
            if 'is not available' in e.message:
                raise UnavailableConvertor(options)
            raise e

    def fetch_acls(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """
        Fetch the ACLs of a document.

        :param uid: the uid of the document
        :return: the ACLs
        """
        req = super(API, self).get(
            path=self._path(uid=uid), cls=dict, headers=self.headers,
            enrichers=['acls'])
        return req['contextParameters']['acls']

    def fetch_audit(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """
        Fetch the audit of a document.

        :param uid: the uid of the document
        :return: the audit
        """
        return super(API, self).get(
            self._path(uid=uid), adapter='audit', cls=dict)

    def fetch_lock_status(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """
        Fetch the lock status of a document.

        :param uid: the uid of the document
        :return: the lock status
        """
        headers = self.headers or {}
        headers.update({'fetch-document': 'lock'})
        req = super(API, self).get(
            path=self._path(uid=uid), cls=dict, headers=headers)
        if 'lockOwner' in req:
            return {
                'lockCreated': req['lockOwner'],
                'lockOwner': req['lockOwner']
            }
        else:
            return {}

    def fetch_rendition(self, uid, name):
        # type: (Text, Text) -> Union[Text, bytes]
        """
        Fetch a rendition of a document.

        :param uid: the uid of the document
        :param name: the name of the rendition
        :return: the corresponding rendition
        """
        adapter = 'rendition/{}'.format(name)
        return super(API, self).get(
            path=self._path(uid=uid), raw=True, adapter=adapter)

    def fetch_renditions(self, uid):
        # type: (Text) -> List[Union[Text, bytes]]
        """
        Fetch all renditions of a document.

        :param uid: the uid of a document
        :return: the renditions
        """
        headers = self.headers or {}
        headers.update({'enrichers-document': 'renditions'})

        req = super(API, self).get(
            path=self._path(uid=uid), cls=dict, headers=headers)
        return [rend['name']
                for rend in req['contextParameters']['renditions']]

    def follow_transition(self, uid, name):
        # type: (Text, Text) -> Dict[Text, Any]
        """
        Follow a lifecycle transition.

        :param uid: the uid of the target document
        :param name: the name of the transition
        """
        params = {'value': name}
        return self.operations.execute(
            command='Document.FollowLifecycleTransition',
            input_obj=uid, params=params)

    def fetch_blob(self, uid=None, path=None, xpath='blobholder:0'):
        # type: (Optional[Text], Optional[Text], Text) -> Blob
        """
        Get the blob of a document.

        :param uid: the uid of the document
        :param path: the path of the document
        :param xpath: the xpath of the blob
        :return: the blob
        """
        adapter = 'blob/{}'.format(xpath)
        return super(API, self).get(
            path=self._path(uid=uid, path=path), raw=True, adapter=adapter)

    def get_children(self, uid=None, path=None):
        # type: (Optional[Text], Optional[Text]) -> List[Document]
        """
        Get the children of a document.

        :param uid: the uid of the document
        :param path: the path of the document
        :return: the document children
        """
        return super(API, self).get(
            path=self._path(uid=uid, path=path), adapter='children')

    def has_permission(self, uid, permission):
        # type: (Text, Text) -> bool
        """
        Check if a document has a permission.

        :param uid: the uid of the document
        :param permission: the permission to check
        :return: True if the document has it, False otherwise
        """
        req = super(API, self).get(
            path=self._path(uid=uid), cls=dict, headers=self.headers,
            enrichers=['permissions'])
        return permission in req['contextParameters']['permissions']

    def lock(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """ Lock a document. """
        return self.operations.execute(
            command='Document.Lock', input_obj=uid)

    def move(self, uid, dst, name=None):
        # type: (Text, Text, Optional[Text]) -> Dict[Text, Any]
        """
        Move a document and eventually rename it.

        :param uid: the uid of the target document
        :param dst: the destination
        :param name: the new name
        """
        params = {'target': dst}
        if name:
            params['name'] = name
        return self.operations.execute(
            command='Document.Move', input_obj=uid, params=params)

    def query(self, opts=None):
        # type: (Optional[Dict[Text, Text]]) -> Dict[Text, Any]
        """
        Run a query on the documents.

        :param opts: a query or a pageProvider
        :return: the corresponding documents
        """
        opts = opts or {}
        if 'query' in opts:
            query = 'NXQL'
        elif 'pageProvider' in opts:
            query = opts['pageProvider']
        else:
            raise BadQuery('Need either a pageProvider or a query')

        path = 'query/{}'.format(query)
        res = super(API, self).get(path=path, params=opts, cls=dict)
        res['entries'] = [Document.parse(entry, service=self)
                          for entry in res['entries']]
        return res

    def remove_permission(self, uid, params):
        # type: (Text, Dict[Text, Text]) -> None
        """
        Remove a permission on a document.

        :param uid: the uid of the document
        :param params: the permission to remove
        """
        self.operations.execute(
            command='Document.RemovePermission', input_obj=uid, params=params)

    def trash(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """
        Trash the document.

        :param uid: the uid of the document
        """
        return self.operations.execute(
            command='Document.Trash', input_obj=uid)

    def unlock(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """ Unlock a document. """
        return self.operations.execute(
            command='Document.Unlock', input_obj=uid)

    def untrash(self, uid):
        # type: (Text) -> Dict[Text, Any]
        """
        Untrash the document.

        :param uid: the uid of the document
        """
        return self.operations.execute(
            command='Document.Untrash', input_obj=uid)

    def workflows(self, document):
        # type: (Document) -> Union[Workflow, List[Workflow]]
        """ Get the workflows of a document. """
        path = 'id/{}/@workflow'.format(document.uid)

        with SwapAttr(self.workflows_api, 'endpoint', self.endpoint):
            return super(WorkflowsAPI, self.workflows_api).get(path=path)

    def _path(self, uid=None, path=None):
        # type: (Optional[Text], Optional[Text]) -> Text
        if uid:
            path = 'repo/{}/id/{}'.format(self.client.repository, uid)
        elif path:
            path = 'repo/{}/path{}'.format(self.client.repository, path)
        return path
