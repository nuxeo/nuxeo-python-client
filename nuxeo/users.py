# coding: utf-8
from .common import NuxeoAutosetObject, NuxeoService


class User(NuxeoAutosetObject):
    """
    Represent a User on the server
    """
    entity_type = 'user'
    def __init__(self, obj=None, service=None, id=None):
        super(User, self).__init__(obj=obj, service=service, id=id)
        self._autoset = True
        self._entity_type = 'user'
        # Avoid change of password on update
        if not self._lazy and 'password' in self.properties:
            del self.properties['password']

    def change_password(self, password):
        """
        Change user password

        :param password: New password to set
        """
        self.properties['password'] = password
        self._service.update(self)


class Users(NuxeoService):
    """
    Users management
    """
    def __init__(self, nuxeo):
        super(Users, self).__init__(nuxeo, 'user', User)
