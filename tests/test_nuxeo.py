# coding: utf-8
from __future__ import unicode_literals

from io import BufferedIOBase
from urllib2 import HTTPError, URLError

import pytest
from nuxeo.blob import Blob


@pytest.mark.parametrize('method, params, is_valid', [
    ('Document.SetBlob', {'file': Blob()}, True),  # 'file' type in [Blob, str]
    ('Document.SetBlob', {'file': 'test.txt'}, True),
    ('Document.SetBlob', {'file': 0}, False),
    ('Document.AddPermission', {'permission': 'Read',
                                'blockInheritance': False}, True),  # 'blockInheritance' type == boolean
    ('Document.AddPermission', {'permission': 'Read',
                                'blockInheritance': 'false'}, False),
    ('Document.AddPermission', {'permission': 'Read', 'end': '01-01-2018'}, True),  # 'end' type == str
    ('Document.AddPermission', {'permission': 'Read', 'end': True}, False),
    ('Document.Fetch', {'value': 'test.txt'}, True),  # 'value' type == str
    ('Document.Fetch', {'value': True}, False),
    ('Document.MultiPublish', {'target': ['test1.txt', 'test2.txt']}, True),  # 'target' type == list
    ('Document.MultiPublish', {'target': 0}, False),
    ('Picture.Resize', {'maxHeight': 100, 'maxWidth': 100}, True),  # 'maxHeight', 'maxWidth' type == int
    ('Picture.Resize', {'maxHeight': 'test', 'maxWidth': 'test'}, False),
    ('Document.Query', {'query': 'test', 'pageSize': 10}, True),  # 'pageSize' type == int
    ('Document.Query', {'query': 'test', 'pageSize': 'test'}, False),
    ('PDF.ExtractPages', {'startPage': 1, 'endPage': 2}, True),  # 'startPage', 'endPage' type == long
    ('PDF.ExtractPages', {'startPage': 'test', 'endPage': 'test'}, False),
    ('User.Invite', {'info': {'username': 'test'}}, True),  # 'info' type == dict
    ('User.Invite', {'info': 0}, False),
    ('Document.Create', {'type': 'Document', 'properties': {'dc:title': 'test'}}, True),  # 'properties' type == dict
    ('Document.Create', {'type': 'Document', 'properties': 0}, False),
    ('Blob.Create', {'file': 'test.txt'}, True),  # 'file' type == str
    ('Blob.Create', {'file': 0}, False),
    ('Document.SetProperty', {'xpath': 'test', 'value': 'test'}, True),  # 'value' type == Sequence
    ('Document.SetProperty', {'xpath': 'test', 'value': [0, 1, 2]}, True),
    ('Document.SetProperty', {'xpath': 'test', 'value': 0}, False),
    ('Document.Query', {'query': 'test'}, True),  # 'query' type == str
    ('Document.Query', {'query': 0}, False),
    ('Document.Query', {'query': 'test', 'queryParams': ['a', 'b', 'c']}, True),  # 'queryParams' type in [list, str]
    ('Document.Query', {'query': 'test', 'queryParams': 'test'}, True),
    ('Document.Query', {'query': 'test', 'queryParams': 0}, False),
    ('User.Invite', {'validationMethod': 'test'}, True),  # 'validationMethod' type == str
    ('User.Invite', {'validationMethod': 0}, False)
])
def test_check_params(method, params, is_valid, server):
    if is_valid:
        server.check_params(method, params)
    else:
        with pytest.raises(TypeError):
            server.check_params(method, params)


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
    rest_url = server.rest_url
    server.rest_url = 'http://localhost:8080/'

    try:
        with pytest.raises(HTTPError) as e:
            server.repository().fetch('/')
        assert e.value.code == 404
    finally:
        server.rest_url = rest_url


def test_get_operations(server):
    assert server.operations


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
    assert server.login()


def test_server_reachable(server):
    assert server.server_reachable()
    base_url = server.base_url
    server.base_url = 'http://example.org/'

    try:
        assert not server.server_reachable()
    finally:
        server.base_url = base_url
