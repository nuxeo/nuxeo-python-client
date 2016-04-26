__author__ = 'loopingz'


class User(object):

    def __init__(self, obj=None, service=None):
        self._entity_type = 'user'
        self._users = service
        if obj is None:
            self.id = None
            self.properties = dict()
        elif isinstance(obj, dict):
            self.id = obj['id']
            self.properties = obj['properties']
        # Avoid change of password on update
        if 'password' in self.properties:
            del self.properties['password']

    def save(self):
        self._users.update(self)

    def delete(self):
        self._users.delete(self.id)

    def change_password(self, password):
        self.properties['password'] = password
        self._users.update(self)

    def __getattr__(self, item):
        if isinstance(item, str) and item in self.properties:
            return self.properties[item]
        raise AttributeError


class Users(object):
    """
    Users management
    """
    def __init__(self, nuxeo):
        self._nuxeo = nuxeo

    def fetch(self, username):
        return User(self._nuxeo.request('user/' + username), self)

    def delete(self, username):
        self._nuxeo.request('user/' + username, method='DELETE')

    def update(self, user):
        self._nuxeo.request('user/' + user.id, body={'entity-type': 'user', 'properties': user.properties, 'id': user.id}, method='PUT')

    def create(self, user):
        if isinstance(user, User):
            properties = user.properties
        elif isinstance(user, dict):
            properties = user
        else:
            raise Exception("Need a dictionary of properties or a User object")
        return User(self._nuxeo.request('user', method='POST', body={'entity-type': 'user', 'properties': properties}), self)