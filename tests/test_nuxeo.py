# coding: utf-8
from __future__ import unicode_literals

from io import BufferedIOBase
from urllib2 import HTTPError, URLError

import pytest


def test_drive_config(monkeypatch, server):

    def mock_server_error(*args, **kwargs):
        raise URLError('Mock error')

    def mock_invalid_response(*args, **kwargs):
        return BufferedIOBase()

    config = server.drive_config()
    assert isinstance(config, dict)
    if config:
        assert 'beta_channel' in config
        assert 'delay' in config
        assert 'handshake_timeout' in config
        assert 'log_level_file' in config
        assert 'timeout' in config
        assert 'update_check_delay' in config
        assert 'ui' in config

    monkeypatch.setattr(server.opener, 'open', mock_server_error)
    assert not server.drive_config()
    monkeypatch.undo()
    monkeypatch.setattr(server.opener, 'open', mock_invalid_response)
    assert not server.drive_config()
    monkeypatch.undo()


def test_encoding_404_error(server):
    rest_url = server._rest_url
    server._rest_url = 'http://localhost:8080/'

    try:
        with pytest.raises(HTTPError) as e:
            server.repository().fetch('/')
        assert e.value.code == 404
    finally:
        server._rest_url = rest_url


def test_get_operations(server):
    assert len(server.operations) > 0


def test_headers(server):
    server.header('Add1', 'Value1')
    headers = server.headers()
    assert headers['Add1'] == 'Value1'
    extras = {
        'Add2': 'Value2',
        'Add1': 'Value3',
    }
    headers = server.headers(extras)
    assert headers['Add2'] == 'Value2'
    assert headers['Add1'] == 'Value3'


def test_login(server):
    user = server.login()
    assert user is not None


def test_server_reachable(server):
    assert server.server_reachable()
    base_url = server.base_url
    server.base_url = 'http://example.org/'

    try:
        assert not server.server_reachable()
    finally:
        server.base_url = base_url
