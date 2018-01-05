# coding: utf-8
from __future__ import unicode_literals

from requests.auth import AuthBase


class TokenAuth(AuthBase):
    """ Attaches Nuxeo Token Authentication to the given Request object. """

    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return self.token == getattr(other, 'token', None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['X-Authentication-Token'] = self.token
        return r
