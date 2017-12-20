# coding: utf-8
from __future__ import unicode_literals

from requests import HTTPError

try:
    from typing import Any, Dict, Optional, Text, Type, Union
except ImportError:
    pass

__all__ = ('NuxeoAutosetObject', 'NuxeoObject', 'NuxeoService')


class NuxeoObject(object):

    def __init__(self, obj=None, service=None, id=None):
        # type: (Optional[Any], Optional[Union[NuxeoService, Repository, Workflows]], Optional[Text]) -> None
        self._dirty = True
        self._lazy = False
        self.service = service
        if obj is None:
            self.id = id
            self.properties = dict()
            self._lazy = True
        elif isinstance(obj, dict):
            self._lazy = False
            self.id = obj.get('id', id)
            self.properties = obj.get('properties', dict())
        self._dirty = False

    def __repr__(self):
        # type: () -> Text
        ret = ', '.join('{}={!r}'.format(*item) for item in vars(self).items()
                        if not item[0].startswith('_'))
        return u'<{}({})>'.format(type(self).__name__, ret)

    def delete(self):
        # type: () -> None
        self.service.delete(self.get_id())

    def get_id(self):
        # type: () -> Text
        return self.id

    def is_lazy(self):
        # type: () -> bool
        return self._lazy

    def load(self):
        # type: () -> None
        self._lazy = False
        self._duplicate(self.service.get(self.get_id()))

    def save(self):
        # type: () -> None
        self.service.update(self)

    def _duplicate(self, obj):
        # type: (Dict[Text, Any]) -> None
        self.properties = obj['properties']


class NuxeoAutosetObject(NuxeoObject):

    def __init__(self, **kwargs):
        # type: (**Any) -> None
        self._autoset = False
        super(NuxeoAutosetObject, self).__init__(**kwargs)

    def __getattr__(self, item):
        # type: (str) -> Text
        if hasattr(self, item) or item.startswith('_'):
            return super(NuxeoObject, self).__getattribute__(item)
        if self._lazy:
            raise RuntimeError(
                'Lazy loading is not yet implemented - use load()')
        if self._autoset and item in self.properties:
            return self.properties[item]
        raise AttributeError

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        if name.startswith('_'):
            super(NuxeoObject, self).__setattr__(name, value)
            return
        if not self._dirty:
            self._dirty = True
        if self._autoset and not hasattr(self, name):
            self.properties[name] = value
        else:
            super(NuxeoObject, self).__setattr__(name, value)


class NuxeoService(object):
    """ Default service. """

    def __init__(self, nuxeo, path, object_class):
        # type: (Nuxeo, Text, Type[NuxeoAutosetObject]) -> None
        self._nuxeo = nuxeo
        self._path = path
        self._object_class = object_class

    def create(self, obj):
        # type: (Union[NuxeoAutosetObject, Dict[Text, Any]]) -> NuxeoAutosetObject
        if isinstance(obj, self._object_class):
            properties = obj.properties
        elif isinstance(obj, dict):
            properties = obj
        else:
            err = 'Need a dictionary of properties or a {} object'
            raise ValueError(err.format(self._object_class))

        body = {
            'entity-type': self._object_class.entity_type,
            'properties': properties,
        }
        req = self._nuxeo.request(self._path, method='POST', body=body)
        return self._object_class(req, self)

    def delete(self, uid):
        # type: (Text) -> None
        self._nuxeo.request(self._path + '/' + uid, method='DELETE')

    def exists(self, uid):
        # type: (Text) -> bool
        try:
            self.fetch(uid)
            return True
        except HTTPError as e:
            if e.response.status_code != 404:
                raise e
        return False

    def fetch(self, uid):
        # type: (Text) -> NuxeoAutosetObject
        return self._object_class(obj=self.get(uid), service=self)

    def get(self, uid):
        # type: (Text) -> Dict[Text, Any]
        return self._nuxeo.request(self._path + '/' + uid)

    def update(self, obj):
        # type: (NuxeoObject) -> None
        body = {
            'entity-type': self._object_class.entity_type,
            'properties': obj.properties,
            'id': obj.get_id(),
        }
        self._nuxeo.request(
            self._path + '/' + obj.get_id(), body=body, method='PUT')
