__author__ = 'loopingz'
from common import NuxeoObject
from common import NuxeoService


class Group(NuxeoObject):

    entity_type = 'group'
    def __init__(self, obj=None, service=None):
        super(Group, self).__init__(obj, service)
        self._entity_type = 'group'
        self.groupname = obj['groupname']
        self.grouplabel = obj['grouplabel']
        if 'memberGroups' in obj:
            self.memberGroups = obj['memberGroups']
        else:
            self.memberGroups = []
        if 'memberUsers' in obj:
            self.memberUsers = obj['memberUsers']
        else:
            self.memberUsers = []

    def get_id(self):
        return self.groupname


class Groups(NuxeoService):
    """
    Users management
    """
    def __init__(self, nuxeo):
        super(Groups, self).__init__(nuxeo, 'group', Group)
        self._query = "?fetch.group=memberUsers&fetch.group=memberGroups"

    def _get_args(self, obj):
        args = {'entity-type': self._object_class.entity_type}
        if isinstance(obj, self._object_class):
            args['groupname'] = obj.groupname
            args['grouplabel'] = obj.grouplabel
            args['memberUsers'] = obj.memberUsers
            args['memberGroups'] = obj.memberGroups
        elif isinstance(obj, dict):
            for key in obj:
                args[key] = obj[key]
        else:
            raise Exception("Need a dictionary of properties or a " + self._object_class + " object")
        return args

    def get(self, id):
        return self._nuxeo.request(self._path + '/' + id + self._query)

    def update(self, obj):
        args = self._get_args(obj)
        self._nuxeo.request(self._path + '/' + obj.get_id() + self._query, body=args, method='PUT', content_type="application/json")

    def create(self, obj):
        args = self._get_args(obj)
        return self._object_class(self._nuxeo.request(self._path + self._query, method='POST', body=args, content_type="application/json"), self)