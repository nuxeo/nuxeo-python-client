# coding: utf-8
from __future__ import unicode_literals


class NuxeoObject(object):

    def __init__(self, obj=None, service=None, id=None):
        self._dirty = True
        self._lazy = False
        self._service = service
        if obj is None:
            self.id = id
            self.properties = dict()
            self._lazy = True
        elif isinstance(obj, dict):
            self._lazy = False
            if 'id' in obj:
                self.id = obj['id']
            if 'properties' in obj:
                self.properties = obj['properties']
            else:
                self.properties = dict()
        self._dirty = False

    def __repr__(self):
        ret = ', '.join('{}={!r}'.format(*item) for item in vars(self).items()
                        if not item[0].startswith('_'))
        return u'<{}({})>'.format(type(self).__name__, ret)

    def is_lazy(self):
        return self._lazy

    def get_id(self):
        return self.id

    def load(self):
        self._lazy = False
        self._duplicate(self._service.get(self.get_id()))

    def _duplicate(self, obj):
        self.properties = obj['properties']

    def save(self):
        self._service.update(self)

    def delete(self):
        self._service.delete(self.get_id())


class NuxeoAutosetObject(NuxeoObject):

    def __init__(self, **kwargs):
        self._autoset = False
        super(NuxeoAutosetObject, self).__init__(**kwargs)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(NuxeoObject, self).__setattr__(name, value)
            return
        if not self._dirty:
            self._dirty = True
        if self._autoset and not hasattr(self, name):
            self.properties[name] = value
        else:
            super(NuxeoObject, self).__setattr__(name, value)

    def __getattr__(self, item):
        if hasattr(self, item):
            return super(NuxeoObject, self).__getattribute__(item)
        if self._lazy:
            raise RuntimeError(
                'Lazy loading is not yet implemented - use load()')
            try:
                self._lazy = False
                self.load()
                if hasattr(self, item):
                    return super(NuxeoObject, self).__getattribute__(item)
            except Exception as e:
                raise e
        if item.startswith('_'):
            return super(NuxeoObject, self).__getattribute__(item)
        if self._autoset and item in self.properties:
            return self.properties[item]
        raise AttributeError


class NuxeoService(object):
    """ Default service. """

    def __init__(self, nuxeo, path, object_class):
        self._nuxeo = nuxeo
        self._path = path
        self._object_class = object_class

    def get(self, uid):
        return self._nuxeo.request(self._path + '/' + uid)

    def fetch(self, uid):
        return self._object_class(obj=self.get(uid), service=self)

    def delete(self, uid):
        self._nuxeo.request(self._path + '/' + uid, method='DELETE')

    def update(self, obj):
        body = {
            'entity-type': self._object_class.entity_type,
            'properties': obj.properties,
            'id': obj.get_id(),
        }
        self._nuxeo.request(
            self._path + '/' + obj.get_id(), body=body, method='PUT')

    def create(self, obj):
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
