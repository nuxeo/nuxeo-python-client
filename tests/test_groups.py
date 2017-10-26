# coding: utf-8
from __future__ import unicode_literals

import time
from urllib2 import HTTPError

from . import NuxeoTest


class TestGroups(NuxeoTest):

    def tearDown(self):
        try:
            self.nuxeo.groups().fetch('plops').delete()
        except:
            pass

    def test_fetch(self):
        group = self.nuxeo.groups().fetch('administrators')
        self.assertIsNotNone(group)

    def test_fetch_unknown_group(self):
        with self.assertRaises(HTTPError) as ex:
            self.nuxeo.groups().fetch('admins')
        self.assertEqual(ex.exception.code, 404)

    def _create_plops(self):
        opts = {'groupname': 'plops',
                'grouplabel': 'Group Test',
                'memberUsers': ['Administrator'],
                'memberGroups': ['Administrators']}
        return self.nuxeo.groups().create(opts)

    def test_create_delete_group_dict(self):
        group = self._create_plops()
        self.assertEqual(group.groupname, 'plops')
        self.assertEqual(group.grouplabel, 'Group Test')
        self.assertEqual(group.memberUsers, ['Administrator'])
        self.assertEqual(group.memberGroups, ['Administrators'])
        group.delete()
        with self.assertRaises(HTTPError) as ex:
            self.nuxeo.groups().fetch('plops')
        self.assertEqual(ex.exception.code, 404)

    def test_update_group(self):
        grouplabel = str(int(round(time.time() * 1000)))
        group = self._create_plops()
        group.grouplabel = grouplabel
        group.save()
        group = self.nuxeo.groups().fetch('plops')
        self.assertEqual(group.grouplabel, grouplabel)
