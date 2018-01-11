# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.users import User


class Georges:

    def __init__(self, server):
        self.server = server

    def __enter__(self):
        user = User(
            properties={
                'lastName': 'Abitbol',
                'firstName': 'Georges',
                'username': 'georges',
                'email': 'georges@example.com',
                'company': 'Pom Pom Gali resort',
                'password': 'Test'
            })
        self.user = self.server.users.create(user)
        return self.user

    def __exit__(self, *args):
        self.user.delete()


def test_create_delete_user_dict(server):
    with Georges(server) as georges:
        assert georges.properties['firstName'] == 'Georges'
        assert georges.properties['lastName'] == 'Abitbol'
        assert georges.properties['company'] == 'Pom Pom Gali resort'
        assert server.users.exists('georges')
    assert not server.users.exists('georges')


def test_create_wrong_arguments(server):
    with pytest.raises(ValueError):
        server.users.create(1)


def test_fetch(server):
    user = server.users.get('Administrator')
    assert user
    assert repr(user)
    assert 'administrators' in user.properties['groups']


def test_fetch_unknown_user(server):
    assert not server.users.exists('Administrator2')


def test_lazy_loading(server):
    with Georges(server):
        user = User(service=server.users, id='georges')
        # TODO Remove when lazy loading is working
        with pytest.raises(KeyError):
            assert user.properties['firstName'] == 'Georges'
        user.load()
        assert user.properties['firstName'] == 'Georges'
        assert user.properties['lastName'] == 'Abitbol'
        assert user.properties['company'] == 'Pom Pom Gali resort'


def test_update_user(server):
    with Georges(server) as georges:
        company = 'Classe Américaine'
        georges.properties['company'] = company
        georges.save()
        user = server.users.get('georges')
        assert user.properties['company'] == company
        auth = server.client.auth
        server.client.auth = ('georges', 'Test')
        try:
            assert server.client.is_reachable()
        finally:
            server.client.auth = auth


def test_update_user_autoset_change_password(server):
    with Georges(server) as georges:
        georges.password = 'Test2'
        georges.save()
        auth = server.client.auth
        server.client.auth = ('georges', 'Test2')
        try:
            assert server.client.is_reachable()
        finally:
            server.client.auth = auth


def test_update_user_autoset_change_password_2(server):
    with Georges(server) as georges:
        georges.change_password('Test3')
        auth = server.client.auth
        server.client.auth = ('georges', 'Test3')
        try:
            assert server.client.is_reachable()
        finally:
            server.client.auth = auth
