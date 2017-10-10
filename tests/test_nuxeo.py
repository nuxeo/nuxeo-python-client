# coding: utf-8
from __future__ import unicode_literals

from .common import NuxeoTest


class LoginTest(NuxeoTest):

    def test_login(self):
        user = self.nuxeo.login()
        self.assertIsNotNone(user)

    def test_headers(self):
        self.nuxeo.header('Add1', 'Value1')
        headers = self.nuxeo.headers()
        self.assertEquals(headers['Add1'], 'Value1')
        extras = {
            'Add2': 'Value2',
            'Add1': 'Value3',
        }
        headers = self.nuxeo.headers(extras)
        self.assertEquals(headers['Add2'], 'Value2')
        self.assertEquals(headers['Add1'], 'Value3')
