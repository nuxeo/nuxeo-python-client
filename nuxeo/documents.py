# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .exceptions import HTTPError, UnavailableConvertor
from .models import Document, Workflow


class API(APIEndpoint):
    def __init__(self, client, operations, endpoint=None, headers=None):
        # type: (NuxeoClient, APIEndpoint, Text, Optional[Dict[Text, Text]]) -> None
        self.operations = operations
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
        return super(API, self).get(request_path=self._path(uid=uid, path=path))

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
            document, request_path=self._path(uid=parent_id, path=parent_path))

    def put(self, document):
        # type: (Document) -> Document
        """
        Update a document.

        :param document: the document to update
        :return: the updated document
        """
        return super(API, self).put(document, request_path=self._path(uid=document.uid))

    def delete(self, document_id):
        # type: (Text) -> Document
        """
        Delete a document.

        :param document_id: the id of the document to delete
        :return: the deleted document
        """
        return super(API, self).delete(self._path(uid=document_id))

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

    def create(self, document, parent_id=None, parent_path=None):
        # type: (Document, Optional[Text], Optional[Text]) -> Document
        """ Alias for self.post(...) """
        return self.post(document, parent_id=parent_id, parent_path=parent_path)

    def add_permission(self, uid, params):
        # type: (Text, Dict[Text, Any]) -> None
        self.operations.execute('Document.AddPermission', input_obj=uid, params=params)

    def convert(self, uid, options):
        # type: (Text, Dict[Text, Text]) -> Union[Text, Dict[Text, Any]]
        """
        Convert a blob into another format.

        :param path: the path of the blob to be converted
        :param options: the target type, target format,
                        or converter for the blob
        :return: the response from the server
        """
        xpath = options.pop('xpath', 'blobholder:0')
        adapter = 'blob/{}/@convert'.format(xpath)
        if ('converter' not in options
                and 'type' not in options
                and 'format' not in options):
            raise ValueError(
                'One of (converter, type, format) is mandatory in options')

        try:
            return super(API, self).get(
                request_path=self._path(uid=uid), params=options, adapter=adapter)
        except HTTPError as e:
            if 'is not registered' in e.message:
                raise ValueError(e.message)
            if 'is not available' in e.message:
                raise UnavailableConvertor(options)
            raise e

    def fetch_acls(self, uid):
        # type: (Text) -> Dict[Text, Any]
        headers = self.headers or {}
        headers.update({'enrichers-document': 'acls'})

        req = super(API, self).get(
            request_path=self._path(uid=uid), resource_cls=dict, headers=headers)
        return req['contextParameters']['acls']

    def fetch_audit(self, uid):
        # type: (Text) -> Dict[Text, Any]
        return super(API, self).get(self._path(uid=uid), adapter='audit', resource_cls=dict)

    def fetch_lock_status(self, uid):
        # type: (Text) -> Dict[Text, Any]
        headers = self.headers or {}
        headers.update({'fetch-document': 'lock'})
        req = super(API, self).get(
            request_path=self._path(uid=uid), resource_cls=dict, headers=headers)
        if 'lockOwner' in req:
            return {
                'lockCreated': req['lockOwner'],
                'lockOwner': req['lockOwner']
            }

    def fetch_rendition(self, uid, name):
        # type: (Text, Text) -> bytes
        adapter = 'rendition/{}'.format(name)
        return super(API, self).get(
            request_path=self._path(uid=uid), raw=True, adapter=adapter)

    def fetch_renditions(self, uid):
        # type: (Text) -> List[Text]
        headers = self.headers or {}
        headers.update({'enrichers-document': 'renditions'})

        req = super(API, self).get(
            request_path=self._path(uid=uid), resource_cls=dict, headers=headers)
        return [rend['name'] for rend in req['contextParameters']['renditions']]

    def follow_transition(self, uid, name):
        # type: (Text, Text) -> None
        """
        Follow a lifecycle transition.

        :param uid: the uid of the target document
        :param name: the name of the transition
        """
        params = {'value': name}
        self.operations.execute(
            'Document.FollowLifecycleTransition', input_obj=uid, params=params)

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
            request_path=self._path(uid=uid, path=path), raw=True, adapter=adapter)

    def get_children(self, uid=None, path=None):
        # type: (Optional[Text], Optional[Text]) -> List[Document]
        """
        Get the children of a document.

        :param uid: the uid of the document
        :param path: the path of the document
        :return: the document children
        """
        return super(API, self).get(
            request_path=self._path(uid=uid, path=path), adapter='children')

    def has_permission(self, uid, permission):
        # type: (Text, Text) -> bool
        headers = self.headers or {}
        headers.update({'enrichers-document': 'permissions'})

        req = super(API, self).get(
            request_path=self._path(uid=uid), resource_cls=dict, headers=headers)
        return permission in req['contextParameters']['permissions']

    def lock(self, uid):
        # type: (Text) -> Dict[Text, Any]
        return self.operations.execute('Document.Lock', input_obj=uid)

    def move(self, uid, dst, name=None):
        # type: (Text, Text, Optional[Text]) -> None
        """
        Move a document and eventually rename it.

        :param uid: the uid of the target document
        :param dst: the destination
        :param name: the new name
        """
        params = {'target': dst}
        if name:
            params['name'] = name
        self.operations.execute('Document.Move', input_obj=uid, params=params)

    def query(self, opts=None):
        # type: (Optional[Dict[Text, Text]]) -> Dict[Text, Any]
        opts = opts or {}
        if 'query' in opts:
            query = 'NXQL'
        elif 'pageProvider' in opts:
            query = opts['pageProvider']
        else:
            raise ValueError('Need either a pageProvider or a query')

        path = 'query/{}'.format(query)
        res = super(API, self).get(request_path=path, params=opts, resource_cls=dict)
        res['entries'] = [Document.parse(entry, service=self) for entry in res['entries']]
        return res

    def remove_permission(self, uid, params):
        # type: (Text, Dict[Text, Text]) -> None
        self.operations.execute('Document.RemovePermission', input_obj=uid, params=params)

    def start_workflow(self, uid, model, options=None):
        # type: (Text, Text, Optional[Dict[Text, Any]]) -> Workflow
        """
        Start a workflow.

        :param uid: the uid of the target document
        :param model: the workflow to start
        :param options: options for the workflow
        :return: the created workflow
        """
        data = {
            'workflowModelName': model,
            'entity-type': 'workflow'
        }
        options = options or {}
        if 'attachedDocumentIds' in options:
            data['attachedDocumentIds'] = options['attachedDocumentIds']
        if 'variables' in options:
            data['variables'] = options['variables']

        self._cls = Workflow
        workflow = super(API, self).post(
            data, request_path=self._path(uid=uid), adapter='workflow')
        self._cls = Document
        return workflow

    def unlock(self, uid):
        # type: (Text) -> Dict[Text, Any]
        return self.operations.execute('Document.Unlock', input_obj=uid)

    def _path(self, uid=None, path=None):
        # type: (Optional[Text], Optional[Text]) -> Text
        if uid:
            request_path = 'repo/{}/id/{}'.format(self.client.repository, uid)
        elif path:
            request_path = 'repo/{}/path{}'.format(self.client.repository, path)
        return request_path
