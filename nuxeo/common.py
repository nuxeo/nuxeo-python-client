__author__ = 'loopingz'


class NuxeoObject(object):

    def __init__(self, obj=None, service=None):
        self._service = service
        if obj is None:
            self.id = None
            self.properties = dict()
        elif isinstance(obj, dict):
            self.id = obj['id']
            self.properties = obj['properties']

    def save(self):
        self._service.update(self)

    def delete(self):
        self._service.delete(self.id)

    def change_password(self, password):
        self.properties['password'] = password
        self._service.update(self)

    def __getattr__(self, item):
        if isinstance(item, str) and item in self.properties:
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

    def fetch(self, username):
        return self._object_class(self._nuxeo.request(self._path + '/' + username), self)

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