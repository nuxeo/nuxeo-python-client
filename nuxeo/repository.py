# coding: utf-8
from __future__ import unicode_literals

from urllib import quote, urlencode

from .document import Document
from .workflow import Workflow

__all__ = ('Repository',)


class Repository(object):
    """
    Repository on Nuxeo allow you to CREATE/GET/UPDATE/DELETE documents
    from the repository.

    You also almost all the method from object Document except you have to
    specify the path or uid of the Document.
    """

    def __init__(self, name, service, schemas=None):
        self._name = name
        self._service = service
        self._schemas = schemas or []

    def _get_path(self, path):
        path = quote(path)
        if path.startswith('/'):
            return 'repo/' + self._name + '/path' + path
        return 'repo/' + self._name + '/id/' + path

    def get(self, path):
        return self._service.request(
            self._get_path(path), extra_headers=self._get_extra_headers())

    def fetch(self, path):
        """
        Get a Document from Nuxeo.

        :param path: path to the Document or its ID.
        :return: Document object.
        """
        return Document(self.get(path), self)

    def fetch_audit(self, path):
        return self._service.request(self._get_path(path) + '/@audit')

    def fetch_blob(self, path, xpath='blobholder:0'):
        return self._service.request(
            self._get_path(path) + '/@blob/' + xpath,
            extra_headers=self._get_extra_headers())

    def fetch_rendition(self, path, name):
        return self._service.request(
            self._get_path(path) + '/@rendition/' + name,
            extra_headers=self._get_extra_headers())

    def fetch_renditions(self, path):
        req = self._service.request(
            self._get_path(path),
            extra_headers={'enrichers-document': 'renditions'})
        return [rend['name']
                for rend in req['contextParameters']['renditions']]

    def fetch_acls(self, path):
        req = self._service.request(
            self._get_path(path),
            extra_headers={'enrichers-document': 'acls'})
        return req['contextParameters']['acls']

    def add_permission(self, uid, params):
        operation = self._service.operation('Document.AddPermission')
        operation.input(uid)
        operation.params(params)
        operation.execute()

    def remove_permission(self, uid, params):
        operation = self._service.operation('Document.RemovePermission')
        operation.input(uid)
        operation.params(params)
        operation.execute()

    def has_permission(self, path, permission):
        req = self._service.request(
            self._get_path(path),
            extra_headers={'enrichers-document': 'permissions'})
        return permission in req['contextParameters']['permissions']

    def fetch_lock_status(self, path):
        ret = dict()
        req = self._service.request(
            self._get_path(path), extra_headers={'fetch-document': 'lock'})
        if 'lockOwner' in req:
            ret['lockCreated'] = req['lockOwner']
            ret['lockOwner'] = req['lockOwner']
        return ret

    def unlock(self, uid):
        operation = self._service.operation('Document.Unlock')
        operation.input(uid)
        return operation.execute()

    def lock(self, uid):
        operation = self._service.operation('Document.Lock')
        operation.input(uid)
        return operation.execute()

    def convert(self, path, options):
        xpath = options['xpath'] if 'xpath' in options else 'blobholder:0'
        path = self._get_path(path) + '/@blob/' + xpath + '/@convert'
        if 'xpath' in options:
            del options['xpath']
        if ('converter' not in options
                and 'type' not in options
                and 'format' not in options):
            raise ValueError(
                'One of (converter, type, format) is mandatory in options')

        path += '?' + urlencode(options, True)
        return self._service.request(path)

    def update(self, obj, uid=None):
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
        req = self._service.request(
            self._get_path(uid), body=body, method='PUT',
            extra_headers=self._get_extra_headers())
        return Document(req, self)

    def _get_extra_headers(self, extras=None):
        extras_header = dict()
        if self._schemas:
            extras_header['X-NXDocumentProperties'] = ','.join(self._schemas)
        extras_header['X-NXRepository'] = self._name
        if extras:
            extras_header.update(extras)
        return extras_header

    def create(self, path, obj):
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
        req = self._service.request(
            self._get_path(path), body=body, method='POST',
            extra_headers=self._get_extra_headers())
        return Document(req, self)

    def delete(self, path):
        """
        Delete a specific Document.

        :param path: Path or ID to the Document.
        """
        self._service.request(self._get_path(path), method='DELETE')

    def query(self, opts=None):
        path = 'query/'
        opts = opts or {}
        if 'query' in opts:
            path += 'NXQL'
        elif 'pageProvider' in opts:
            path += opts['pageProvider']
        else:
            raise ValueError('Need either a pageProvider or a query')

        path += '?' + urlencode(opts, True)
        req = self._service.request(
            path, extra_headers=self._get_extra_headers())

        # Mapping entries to Document
        docs = [Document(doc, self) for doc in req['entries']]
        req['entries'] = docs

        return req

    def follow_transition(self, uid, name):
        operation = self._service.operation(
            'Document.FollowLifecycleTransition')
        operation.input(uid)
        operation.params({'value': name})
        operation.execute()

    def move(self, uid, dst, name=None):
        operation = self._service.operation('Document.Move')
        operation.input(uid)
        params = {'target': dst}
        if name:
            params['name'] = name
        operation.params(params)
        operation.execute()

    def start_workflow(self, name, path, options):
        return self._service.workflows().start(
            name, options, url=self._get_path(path) + '/@workflow')

    def fetch_workflows(self, path):
        req = self._service.request(self._get_path(path) + '/@workflow')
        return self._service.workflows()._map(req, Workflow)
