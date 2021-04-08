# coding: utf-8
from __future__ import unicode_literals

import pytest
from requests import Request

from nuxeo.auth import JWTAuth, PortalSSOAuth, TokenAuth
from nuxeo.auth.utils import make_portal_sso_token
from nuxeo.compat import text
from nuxeo.exceptions import NuxeoError

# We do not need to set-up a server and log the current test
skip_logging = True


def test_jwt():
    auth = JWTAuth("<TOKEN>")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    prepared = req.prepare()
    assert prepared.headers[auth.AUTHORIZATION] == "Bearer <TOKEN>"


def test_jwt_equality():
    auth1 = JWTAuth("secure secret")
    auth2 = JWTAuth("other secret")
    assert auth1 != auth2


def test_make_portal_sso_token():
    timestamp = 1324572561000
    random = "qwertyuiop"
    secret = "secret"
    username = "bob"
    expected = "8y4yXfms/iKge/OtG6d2zg=="
    result = make_portal_sso_token(timestamp, random, secret, username)
    assert result == expected


def test_portal_sso():
    auth = PortalSSOAuth("alice", "secure secret")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    prepared = req.prepare()
    assert prepared.headers[auth.NX_USER] == "alice"
    assert auth.NX_TOKEN in prepared.headers
    assert auth.NX_RD in prepared.headers
    assert auth.NX_TS in prepared.headers


def test_portal_sso_equality():
    auth1 = PortalSSOAuth("alice", "secure secret")
    auth2 = PortalSSOAuth("bob", "secret")
    auth3 = PortalSSOAuth("bob", "secret", digest_algorithm="sha256")
    assert auth1 != auth2
    assert auth2 != auth3


def test_portal_sso_digest_algorithm_uppercase():
    auth = PortalSSOAuth("alice", "secure secret", digest_algorithm="MD5")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    prepared = req.prepare()
    assert prepared.headers[auth.NX_USER] == "alice"
    assert auth.NX_TOKEN in prepared.headers
    assert auth.NX_RD in prepared.headers
    assert auth.NX_TS in prepared.headers


def test_portal_sso_digest_algorithm_not_found():
    auth = PortalSSOAuth("alice", "secure secret", digest_algorithm="boom")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    with pytest.raises(NuxeoError) as exc:
        req.prepare()
    error = text(exc.value)
    msg = "Cannot compute token because of unknown digest algorithm"
    assert msg in error


def test_token():
    auth = TokenAuth("secure_token")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    prepared = req.prepare()
    assert prepared.headers[auth.HEADER_TOKEN] == "secure_token"


def test_token_equality():
    auth1 = TokenAuth("secure_token")
    auth2 = TokenAuth("0")
    assert auth1 != auth2
