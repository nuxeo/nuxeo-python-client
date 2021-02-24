# coding: utf-8
from __future__ import unicode_literals

from requests import Request

# We do not need to set-up a server and log the current test
skip_logging = True


def test_make_portal_sso_token():
    from nuxeo.auth.utils import make_portal_sso_token

    timestamp = 1324572561000
    random = "qwertyuiop"
    secret = "secret"
    username = "bob"
    expected = "8y4yXfms/iKge/OtG6d2zg=="
    result = make_portal_sso_token(timestamp, random, secret, username)
    assert result == expected


def test_nuxeo_token_auth():
    from nuxeo.auth import TokenAuth

    auth = TokenAuth("secure_token")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    prepared = req.prepare()
    assert prepared.headers[auth.HEADER_TOKEN] == "secure_token"


def test_portal_sso_auth():
    from nuxeo.auth import PortalSSOAuth

    auth = PortalSSOAuth("alice", "secure secret")
    req = Request("GET", "https://httpbin.org/get", auth=auth)
    prepared = req.prepare()
    assert prepared.headers[auth.NX_USER] == "alice"
    assert auth.NX_TOKEN in prepared.headers
    assert auth.NX_RD in prepared.headers
    assert auth.NX_TS in prepared.headers
