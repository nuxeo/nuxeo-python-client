# coding: utf-8
from __future__ import unicode_literals

import time

import pytest

from nuxeo.compat import text
from nuxeo.exceptions import BadQuery
from nuxeo.models import Group


def get_group(server):
    group = Group(
        groupname='plops',
        grouplabel='Group Test',
        memberUsers=['Administrator'],
        memberGroups=['Administrators'])
    assert repr(group)
    return server.groups.create(group)


def test_create_delete_group_dict(server):
    get_group(server)
    try:
        group = server.groups.get('plops')
        assert group.groupname == 'plops'
        assert group.grouplabel == 'Group Test'
        assert group.memberUsers == ['Administrator']
        assert group.memberGroups == ['Administrators']
    finally:
        group.delete()
        assert not server.groups.exists('plops')


def test_create_wrong_arguments(server):
    with pytest.raises(BadQuery):
        server.groups.create(1)


def test_fetch(server):
    assert server.groups.get('administrators')


def test_fetch_unknown_group(server):
    assert not server.groups.exists('admins')


def test_update_group(server):
    group = get_group(server)
    try:
        grouplabel = text(int(round(time.time() * 1000)))
        group.grouplabel = grouplabel
        group.save()
        group = server.groups.get('plops')
        assert group.grouplabel == grouplabel
    finally:
        group.delete()
