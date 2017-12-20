# coding: utf-8
from __future__ import unicode_literals

from requests import HTTPError

from .compat import urlencode
from .document import Document
from .exceptions import UnavailableConvertor
from .workflow import Workflow

try:
    from typing import Any, Dict, List, Optional, Text, Union
except ImportError:
    pass

__all__ = ('Repository',)


class Repository(object):
    """
    Repository on Nuxeo allow you to CREATE/GET/UPDATE/DELETE documents
    from the repository.

    You also almost all the method from object Document except you have to
    specify the path or uid of the Document.
    """

    def __init__(self, name, service, schemas=None):
        # type: (Text, Nuxeo, Optional[Text]) -> None
        self._name = name
        self.service = service
        self._schemas = schemas or []

    def add_permission(self, uid, params):
        # type: (Text, Dict[Text, Any]) -> None
        operation = self.service.operation('Document.AddPermission')
        operation.input(uid)
        operation.params(params)
        operation.execute()

    def convert(self, path, options):
        # type: (Text, Dict[Text, Text]) -> Union[Text, Dict[Text, Any]]
        """
        Convert a blob into another format.

        :param path: the path of the blob to be converted
        :param options: the target type, target format,
                        or converter for the blob
        :return: the response from the server
        """
        xpath = options.pop('xpath', 'blobholder:0')
        path = self._get_path(path) + '/@blob/' + xpath + '/@convert'
        if ('converter' not in options
                and 'type' not in options
                and 'format' not in options):
            raise ValueError(
                'One of (converter, type, format) is mandatory in options')

        path += '?' + urlencode(options, True)
        try:
            return self.service.request(path)
        except HTTPError as e:
            resp = e.response.json()
            if 'is not registered' in resp.get('message'):
                raise ValueError(resp.get('message'))
            if 'is not available' in resp.get('message'):
                raise UnavailableConvertor(options)
            raise e

    def create(self, path, obj):
        # type: (Text, Dict[Text, Any]) -> Document
        """
        Create a new Document on the server.

        :param path: Path to create the Document.
        :param dict obj: Document description: at least type, name, properties.
        :rtype: Document
        """

        body = {
            'entity-type': 'document',
            'type': obj['type'],
            'name': obj['name'],
            'properties': obj['properties'],
        }
        req = self.service.request(
            self._get_path(path), body=body, method='POST',
            extra_headers=self._get_extra_headers())
        return Document(req, self)

    def delete(self, path):
        # type: (Text) -> None
        """
        Delete a specific Document.

        :param path: Path or ID to the Document.
        """
        self.service.request(self._get_path(path), method='DELETE')

    def exists(self, path):
        # type: (Text) -> bool
        try:
            self.fetch(path)
            return True
        except HTTPError as e:
            if e.response.status_code != 404:
                raise e
        return False

    def fetch(self, path):
        # type: (Text) -> Document
        """
        Get a Document from Nuxeo.

        :param path: path to the Document or its ID.
        :return: Document object.
        """
        return Document(self.get(path), self)

    def fetch_acls(self, path):
        # type: (Text) -> Dict[Text, Any]
        req = self.service.request(
            self._get_path(path),
            extra_headers={'enrichers-document': 'acls'})
        return req['contextParameters']['acls']

    def fetch_audit(self, path):
        # type: (Text) -> Dict[Text, Any]
        return self.service.request(self._get_path(path), adapter='audit')

    def fetch_blob(self, path, xpath='blobholder:0'):
        # type: (Text, Text) -> Union[Text, Dict[Text, Any], bytes]
        return self.service.request(
            self._get_path(path) + '/@blob/' + xpath,
            extra_headers=self._get_extra_headers())

    def fetch_lock_status(self, path):
        # type: (Text) -> Dict[Text, Any]
        ret = dict()
        req = self.service.request(
            self._get_path(path), extra_headers={'fetch-document': 'lock'})
        if 'lockOwner' in req:
            ret['lockCreated'] = req['lockOwner']
            ret['lockOwner'] = req['lockOwner']
        return ret

    def fetch_rendition(self, path, name):
        # type: (Text, Text) -> bytes
        return self.service.request(
            self._get_path(path) + '/@rendition/' + name,
            extra_headers=self._get_extra_headers())

    def fetch_renditions(self, path):
        # type: (Text) -> List[Text]
        req = self.service.request(
            self._get_path(path),
            extra_headers={'enrichers-document': 'renditions'})
        return [rend['name']
                for rend in req['contextParameters']['renditions']]

    def fetch_workflows(self, path):
        # type: (Text) -> List[Workflow]
        req = self.service.request(self._get_path(path), adapter='workflow')
        return self.service.workflows().map(req, Workflow)

    def follow_transition(self, uid, name):
        # type: (Text, Text) -> None
        operation = self.service.operation(
            'Document.FollowLifecycleTransition')
        operation.input(uid)
        operation.params({'value': name})
        operation.execute()

    def get(self, path):
        # type: (Text) -> Union[Dict[Text, Any], Text, bytes]
        return self.service.request(
            self._get_path(path), extra_headers=self._get_extra_headers())

    def has_permission(self, path, permission):
        # type: (Text, Text) -> bool
        req = self.service.request(
            self._get_path(path),
            extra_headers={'enrichers-document': 'permissions'})
        return permission in req['contextParameters']['permissions']

    def lock(self, uid):
        # type: (Text) -> Dict[Text, Any]
        operation = self.service.operation('Document.Lock')
        operation.input(uid)
        return operation.execute()

    def move(self, uid, dst, name=None):
        # type: (Text, Text, Optional[Text]) -> None
        operation = self.service.operation('Document.Move')
        operation.input(uid)
        params = {'target': dst}
        if name:
            params['name'] = name
        operation.params(params)
        operation.execute()

    def query(self, opts=None):
        # type: (Optional[Dict[Text, Text]]) -> Dict[Text, Any]
        path = 'query/'
        opts = opts or {}
        if 'query' in opts:
            path += 'NXQL'
        elif 'pageProvider' in opts:
            path += opts['pageProvider']
        else:
            raise ValueError('Need either a pageProvider or a query')

        path += '?' + urlencode(opts, True)
        req = self.service.request(
            path, extra_headers=self._get_extra_headers())

        # Mapping entries to Document
        docs = [Document(doc, self) for doc in req['entries']]
        req['entries'] = docs

        return req

    def remove_permission(self, uid, params):
        # type: (Text, Dict[Text, Text]) -> None
        operation = self.service.operation('Document.RemovePermission')
        operation.input(uid)
        operation.params(params)
        operation.execute()

    def start_workflow(self, name, path, options):
        # type: (Text, Text, Dict[Text, Text]) -> Workflow
        return self.service.workflows().start(
            name, options, url=self._get_path(path) + '/@workflow')

    def unlock(self, uid):
        # type: (Text) -> Dict[Text, Any]
        operation = self.service.operation('Document.Unlock')
        operation.input(uid)
        return operation.execute()

    def update(self, obj, uid=None):
        # type: (Union[Document, Dict[Text, Any]], Optional[Text]) -> Document
        if isinstance(obj, Document):
            properties = obj.properties
            uid = obj.get_id()
        elif isinstance(obj, dict):
            properties = obj
        else:
            raise ValueError(
                'Argument should be either a dict or a Document object')

        body = {
            'entity-type': 'document',
            'uid': uid,
            'properties': properties
        }
        req = self.service.request(
            self._get_path(uid), body=body, method='PUT',
            extra_headers=self._get_extra_headers())
        return Document(req, self)

    def _get_extra_headers(self, extras=None):
        # type: (Optional[Dict[Text, Text]]) -> Dict[Text, Text]
        extras_header = {'X-NXRepository': self._name}
        if self._schemas:
            extras_header['X-NXDocumentProperties'] = ','.join(self._schemas)
        if extras:
            extras_header.update(extras)
        return extras_header

    def _get_path(self, path):
        # type: (Text) -> Text
        if path.startswith('/'):
            return 'repo/' + self._name + '/path' + path
        return 'repo/' + self._name + '/id/' + path
