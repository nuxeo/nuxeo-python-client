# coding: utf-8
import pytest
from nuxeo.auth import BasicAuth
from nuxeo.client import Nuxeo
from nuxeo.exceptions import BadQuery
from nuxeo.users import User
from ..constants import SSL_VERIFY


class Georges(object):
    def __init__(self, server):
        self.server = server

    def __enter__(self):
        existed_user = None
        try:
            existed_user = self.server.users.get("georges", ssl_verify=SSL_VERIFY)
            existed_user.delete()
        finally:
            user = User(
                properties={
                    "lastName": "Abitbol",
                    "firstName": "Georges",
                    "username": "georges",
                    "email": "georges@example.com",
                    "company": "Pom Pom Gali resort",
                    "password": "Test",
                }
            )
            self.user = self.server.users.create(user, ssl_verify=SSL_VERIFY)
            return self.user

    def __exit__(self, *args):
        self.user.delete()


def test_create_delete_user_dict(server):
    with Georges(server) as georges:
        assert georges.properties["firstName"] == "Georges"
        assert georges.properties["lastName"] == "Abitbol"
        assert georges.properties["company"] == "Pom Pom Gali resort"
        assert server.users.exists("georges", ssl_verify=SSL_VERIFY)
    assert not server.users.exists("georges", ssl_verify=SSL_VERIFY)


def test_create_wrong_arguments(server):
    with pytest.raises(BadQuery):
        server.users.create(1, ssl_verify=SSL_VERIFY)


def test_current_user(server):
    user = server.users.current_user(ssl_verify=SSL_VERIFY)
    assert isinstance(user, User)
    assert user.uid == "Administrator"
    assert "administrators" in [g["name"] for g in user.extendedGroups]
    assert user.isAdministrator


def test_fetch(server):
    user = server.users.get("Administrator", ssl_verify=SSL_VERIFY)
    assert user
    assert repr(user)
    assert "administrators" in user.properties["groups"]


def test_fetch_unknown_user(server):
    assert not server.users.exists("Administrator2", ssl_verify=SSL_VERIFY)


def test_lazy_loading(server):
    with Georges(server):
        user = User(service=server.users, id="georges")
        # TODO Remove when lazy loading is working
        with pytest.raises(KeyError):
            assert user.properties["firstName"] == "Georges"
        user.load()
        assert user.properties["firstName"] == "Georges"
        assert user.properties["lastName"] == "Abitbol"
        assert user.properties["company"] == "Pom Pom Gali resort"


def test_update_user(server, host):
    with Georges(server) as georges:
        company = "Classe Américaine"
        georges.properties["company"] = company
        georges.save()
        user = server.users.get("georges", ssl_verify=SSL_VERIFY)
        assert user.properties["company"] == company

        auth = BasicAuth("georges", "Test")
        server2 = Nuxeo(host=host, auth=auth)
        assert server2.users.current_user(ssl_verify=SSL_VERIFY)


def test_update_user_autoset_change_password(server, host):
    with Georges(server) as georges:
        georges.change_password("Test2")
        georges.save()

        auth = BasicAuth("georges", "Test2")
        server2 = Nuxeo(host=host, auth=auth)
        assert server2.users.current_user(ssl_verify=SSL_VERIFY)
