# coding: utf-8
from __future__ import unicode_literals

from .common import NuxeoObject, NuxeoService


class Group(NuxeoObject):
    """ Represent a Group on the server. """

    entity_type = 'group'

    def __init__(self, obj=None, service=None):
        super(Group, self).__init__(obj, service)
        self._entity_type = 'group'
        self.groupname = obj['groupname']
        self.grouplabel = obj['grouplabel']
        self.memberGroups = obj.get('memberGroups', [])
        self.memberUsers = obj.get('memberUsers', [])

    def get_id(self):
        return self.groupname


class Groups(NuxeoService):
    """ Groups management. """

    def __init__(self, nuxeo):
        super(Groups, self).__init__(nuxeo, 'group', Group)
        self._query = '?fetch.group=memberUsers&fetch.group=memberGroups'

    def _get_args(self, obj):
        args = {'entity-type': self._object_class.entity_type}
        if isinstance(obj, self._object_class):
            args['groupname'] = obj.groupname
            args['grouplabel'] = obj.grouplabel
            args['memberUsers'] = obj.memberUsers
            args['memberGroups'] = obj.memberGroups
        elif isinstance(obj, dict):
            args.update(obj)
        else:
            err = 'Need a dictionary of properties or a {} object'
            raise ValueError(err.format(self._object_class))
        return args

    def get(self, uid):
        """
        Get a group.

        :param uid: Group name
        :return:
        """
        return self._nuxeo.request(self._path + '/' + uid + self._query)

    def update(self, obj):
        """
        Update the group.

        :param obj: Group object
        """
        args = self._get_args(obj)
        self._nuxeo.request(self._path + '/' + obj.get_id() + self._query,
                            body=args, method='PUT')

    def create(self, obj):
        """
        Create a new group.

        :param obj:
        :return: Group created
        """
        args = self._get_args(obj)
        req = self._nuxeo.request(
            self._path + self._query, method='POST', body=args)
        return self._object_class(req, self)
