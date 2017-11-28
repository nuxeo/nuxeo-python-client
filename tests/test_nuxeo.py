# coding: utf-8
from __future__ import unicode_literals

from io import BufferedIOBase
from urllib2 import HTTPError, URLError

import pytest

from nuxeo import Nuxeo
from . import NuxeoTest


class TestNuxeo(NuxeoTest):
    def test_get_operations(self):
        self.assertGreater(len(self.nuxeo.operations), 0)

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

    def test_login(self):
        user = self.nuxeo.login()
        self.assertIsNotNone(user)

    def test_server_reachable(self):
        self.assertTrue(self.nuxeo.server_reachable())
        base_url = self.nuxeo.base_url
        self.nuxeo.base_url = 'http://example.org/'
        try:
            self.assertFalse(self.nuxeo.server_reachable())
        finally:
            self.nuxeo.base_url = base_url


def test_encoding_404_error():
    nuxeo = Nuxeo(
        base_url='http://localhost:8080/',
        auth={
            'username': 'Administrator',
            'password': 'Administrator'
        })

    with pytest.raises(HTTPError) as e:
        nuxeo.repository().fetch('/')

    assert e.value.code == 404


def test_drive_config(monkeypatch):
    nuxeo = Nuxeo(
        base_url='http://localhost:8080/nuxeo',
        auth={
            'username': 'Administrator',
            'password': 'Administrator'
        })

    def mock_server_error(*args, **kwargs):
        raise URLError('Mock error')

    def mock_invalid_response(*args, **kwargs):
        return BufferedIOBase()

    config = nuxeo.drive_config()
    assert isinstance(config, dict)
    if config:
        assert 'beta_channel' in config
        assert 'delay' in config
        assert 'handshake_timeout' in config
        assert 'log_level_file' in config
        assert 'timeout' in config
        assert 'update_check_delay' in config
        assert 'ui' in config

    monkeypatch.setattr(nuxeo.opener, 'open', mock_server_error)
    assert not nuxeo.drive_config()
    monkeypatch.undo()
    monkeypatch.setattr(nuxeo.opener, 'open', mock_invalid_response)
    assert not nuxeo.drive_config()
    monkeypatch.undo()
