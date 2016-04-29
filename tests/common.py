__author__ = 'loopingz'
from unittest import TestCase
from nuxeo.nuxeo import Nuxeo

class NuxeoTest(TestCase):

    def setUp(self):
        self._nuxeo =  Nuxeo("http://localhost:8080/nuxeo", auth={'username': 'Administrator', 'password': 'Administrator'})