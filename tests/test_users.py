# coding: utf-8
from __future__ import unicode_literals

import time

import pytest

from nuxeo.nuxeo import Nuxeo
from nuxeo.users import User


def create_georges(server):
    opts = {
        'lastName': 'Abitbol',
        'firstName': 'Georges',
        'username': 'georges',
        'company': 'Pom Pom Gali resort',
        'password': 'Test'}
    return server.users().create(opts)


def test_create_delete_user_dict(server):
    opts = {
        'lastName': 'Abitbol',
        'firstName': 'Georges',
        'username': 'georges',
        'company': 'Pom Pom Gali resort'}
    user = server.users().create(opts)
    assert user.properties['firstName'] == 'Georges'
    assert user.properties['lastName'] == 'Abitbol'
    assert user.properties['company'] == 'Pom Pom Gali resort'
    user.delete()
    assert not server.users().exists('georges')


def test_fetch(server):
    user = server.users().fetch('Administrator')
    assert user
    assert 'administrators' in user.properties['groups']


def test_fetch_unknown_user(server):
    assert not server.users().exists('Administrator2')


def test_lazy_loading(server):
    create_georges(server)
    user = User(service=server.users(), id='georges')
    # TODO Remove when lazy loading is working
    with pytest.raises(RuntimeError):
        assert user.firstName == 'Georges'
    user.load()
    assert user.properties['firstName'] == 'Georges'
    assert user.properties['lastName'] == 'Abitbol'
    assert user.properties['company'] == 'Pom Pom Gali resort'
    user.delete()


def test_update_user(server):
    company = str(int(round(time.time() * 1000)))
    user = create_georges(server)
    user.properties['company'] = company
    user.save()
    user = server.users().fetch('georges')
    assert user.properties['company'] == company
    auth = {'username': 'georges', 'password': 'Test'}
    nuxeo = Nuxeo(server.base_url, auth=auth)
    assert nuxeo.login()
    user.delete()


def test_update_user_autoset_change_password(server):
    user = create_georges(server)
    user.password = 'Test2'
    user.save()
    server.users().fetch('georges')
    auth = {'username': 'georges', 'password': 'Test2'}
    nuxeo = Nuxeo(server.base_url, auth=auth)
    assert nuxeo.login()
    user.delete()


def test_update_user_autoset_change_password_2(server):
    user = create_georges(server)
    user.change_password('Test3')
    auth = {'username': 'georges', 'password': 'Test3'}
    nuxeo = Nuxeo(server.base_url, auth=auth)
    assert nuxeo.login()
    user.delete()
