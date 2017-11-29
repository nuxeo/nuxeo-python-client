# coding: utf-8
from __future__ import unicode_literals

import time


def create_plops(server):
    opts = {'groupname': 'plops',
            'grouplabel': 'Group Test',
            'memberUsers': ['Administrator'],
            'memberGroups': ['Administrators']}
    return server.groups().create(opts)


def test_create_delete_group_dict(server):
    group = create_plops(server)
    assert group.groupname == 'plops'
    assert group.grouplabel == 'Group Test'
    assert group.memberUsers == ['Administrator']
    assert group.memberGroups == ['Administrators']
    group.delete()
    assert not server.groups().exists('plops')


def test_fetch(server):
    group = server.groups().fetch('administrators')
    assert group is not None


def test_fetch_unknown_group(server):
    assert not server.groups().exists('admins')


def test_update_group(server):
    grouplabel = str(int(round(time.time() * 1000)))
    group = create_plops(server)
    group.grouplabel = grouplabel
    group.save()
    group = server.groups().fetch('plops')
    assert group.grouplabel == grouplabel
    group.delete()
