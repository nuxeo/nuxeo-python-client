__author__ = 'loopingz'
from common import NuxeoObject
from common import NuxeoService


class User(NuxeoObject):

    entity_type = 'user'
    def __init__(self, obj=None, service=None):
        super(User, self).__init__(obj, service)
        self._entity_type = 'user'
        # Avoid change of password on update
        if 'password' in self.properties:
            del self.properties['password']


class Users(NuxeoService):
    """
    Users management
    """
    def __init__(self, nuxeo):
        super(Users, self).__init__(nuxeo, 'user', User)
