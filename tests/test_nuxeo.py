__author__ = 'loopingz'

from unittest import TestCase
from nuxeo.nuxeo import Nuxeo


class NuxeoTest(TestCase):

    def setUp(self):
        self._nuxeo =  Nuxeo("http://localhost:8080/nuxeo", auth={'username': 'Administrator', 'password': 'Administrator'})

    def test_login(self):
        user = self._nuxeo.login()
        self.assertIsNotNone(user)

    def test_headers(self):
        self._nuxeo.header('Add1', 'Value1')
        headers = self._.headers()
        self.assertEquals(headers['Add1'], 'Value1')
        extras = dict()
        extras['Add2'] = 'Value2'
        extras['Add1'] = 'Value3'
        headers = self._.headers(extras)
        self.assertEquals(headers['Add2'], 'Value2')
        self.assertEquals(headers['Add1'], 'Value3')