# coding: utf-8
from __future__ import unicode_literals

import time

import pytest

from nuxeo.compat import text
from nuxeo.nuxeo import Nuxeo
from nuxeo.users import User


def test_create_delete_user_dict(server, georges):
    assert georges.properties['firstName'] == 'Georges'
    assert georges.properties['lastName'] == 'Abitbol'
    assert georges.properties['company'] == 'Pom Pom Gali resort'
    assert server.users().exists('georges')
    georges.delete()
    assert not server.users().exists('georges')


def test_create_wrong_arguments(server):
    with pytest.raises(ValueError):
        server.users().create(1)


def test_fetch(server):
    user = server.users().fetch('Administrator')
    assert user
    assert 'administrators' in user.properties['groups']


def test_fetch_unknown_user(server):
    assert not server.users().exists('Administrator2')


def test_lazy_loading(server, georges):
    user = User(service=server.users(), id='georges')
    # TODO Remove when lazy loading is working
    with pytest.raises(RuntimeError):
        assert user.firstName == 'Georges'
    user.load()
    assert user.properties['firstName'] == 'Georges'
    assert user.properties['lastName'] == 'Abitbol'
    assert user.properties['company'] == 'Pom Pom Gali resort'
    user.delete()


def test_update_user(server, georges):
    company = text(int(round(time.time() * 1000)))
    georges.properties['company'] = company
    georges.save()
    user = server.users().fetch('georges')
    assert user.properties['company'] == company
    auth = {'username': 'georges', 'password': 'Test'}
    nuxeo = Nuxeo(server.base_url, auth=auth)
    assert nuxeo.login()
    user.delete()


def test_update_user_autoset_change_password(server, georges):
    georges.password = 'Test2'
    georges.save()
    server.users().fetch('georges')
    auth = {'username': 'georges', 'password': 'Test2'}
    nuxeo = Nuxeo(server.base_url, auth=auth)
    assert nuxeo.login()
    georges.delete()


def test_update_user_autoset_change_password_2(server, georges):
    georges.change_password('Test3')
    auth = {'username': 'georges', 'password': 'Test3'}
    nuxeo = Nuxeo(server.base_url, auth=auth)
    assert nuxeo.login()
    georges.delete()
