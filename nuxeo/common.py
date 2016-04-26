__author__ = 'loopingz'


class NuxeoObject(object):

    def __init__(self, obj=None, service=None, id=None):
        self._dirty = True
        self._autoset = False
        self._service = service
        if obj is None:
            self._lazy = True
            self.id = id
            self.properties = dict()
        elif isinstance(obj, dict):
            self._lazy = False
            if 'id' in obj:
                self.id = obj['id']
            if 'properties' in obj:
                self.properties = obj['properties']
        self._dirty = False

    def is_lazy(self):
        return self._lazy

    def _get(self):
        self._duplicate(self._service.get(self.id))

    def _duplicate(self, obj):
        self.properties = obj.properties

    def save(self):
        self._service.update(self)

    def delete(self):
        self._service.delete(self.id)

    def change_password(self, password):
        self.properties['password'] = password
        self._service.update(self)

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
        if item in self.properties:
            return self.properties[item]
        raise AttributeError



class NuxeoService(object):
    """
    Default service
    """
    def __init__(self, nuxeo, path, object_class):
        self._nuxeo = nuxeo
        self._path = path
        self._object_class = object_class

    def fetch(self, id):
        return self._object_class(self._nuxeo.request(self._path + '/' + id), self)

    def delete(self, id):
        self._nuxeo.request(self._path + '/' + id, method='DELETE')

    def update(self, obj):
        self._nuxeo.request(self._path + '/' + obj.id, body={'entity-type': 'user', 'properties': obj.properties, 'id': obj.id}, method='PUT')

    def create(self, obj):
        if isinstance(obj, self._object_class):
            properties = obj.properties
        elif isinstance(obj, dict):
            properties = obj
        else:
            raise Exception("Need a dictionary of properties or a User object")
        return self._object_class(self._nuxeo.request('user', method='POST', body={'entity-type': self._object_class.entity_type, 'properties': properties}), self)