# coding: utf-8
from __future__ import unicode_literals

import pytest
import time


@pytest.fixture(scope='function')
def group(server):
    opts = {'groupname': 'plops',
            'grouplabel': 'Group Test',
            'memberUsers': ['Administrator'],
            'memberGroups': ['Administrators']}
    return server.groups().create(opts)


def test_create_delete_group_dict(server, group):
    assert group.groupname == 'plops'
    assert group.grouplabel == 'Group Test'
    assert group.memberUsers == ['Administrator']
    assert group.memberGroups == ['Administrators']
    group.delete()
    assert not server.groups().exists('plops')


def test_create_wrong_arguments(server):
    with pytest.raises(ValueError):
        server.groups().create(1)


def test_fetch(server):
    assert server.groups().fetch('administrators')


def test_fetch_unknown_group(server):
    assert not server.groups().exists('admins')


def test_update_group(server, group):
    grouplabel = str(int(round(time.time() * 1000)))
    group.grouplabel = grouplabel
    group.save()
    group = server.groups().fetch('plops')
    assert group.grouplabel == grouplabel
    group.delete()
