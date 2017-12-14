# coding: utf-8
from __future__ import unicode_literals

import json
import os

import pytest
import requests
from requests import HTTPError

from nuxeo.blob import Blob
from nuxeo.exceptions import Unauthorized
from nuxeo.nuxeo import Nuxeo


@pytest.mark.parametrize('method, params, is_valid', [
    ('Document.SetBlob', {'file': Blob()}, True),  # 'file' type in (Blob, str)
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
    ('Audit.Query', {'query': 'test', 'pageNo': 100}, True),  # 'pageNo' type == int
    ('Audit.Query', {'query': 'test', 'pageNo': 'test'}, False),
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
    ('User.Invite', {'validationMethod': 0}, False),
])
def test_check_params(method, params, is_valid, server):
    if is_valid:
        server.check_params(method, params)
    else:
        with pytest.raises(TypeError):
            server.check_params(method, params)


def test_check_params_unknown_operation(server):
    with pytest.raises(ValueError):
        server.check_params('alien', {})


def test_drive_config(monkeypatch, server):

    def mock_server_error(*args, **kwargs):
        def mock_HTTP():
            return HTTPError('Mock error')
        mock_response = requests.Response()
        mock_response.status_code = 404
        mock_response.raise_for_status = mock_HTTP
        return mock_response

    def mock_invalid_response(*args, **kwargs):
        return requests.Response()

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

    monkeypatch.setattr(requests.Session, 'request', mock_server_error)
    assert not server.drive_config()
    monkeypatch.undo()
    monkeypatch.setattr(requests.Session, 'request', mock_invalid_response)
    assert not server.drive_config()
    monkeypatch.undo()


def test_encoding_404_error(server):
    rest_url = server.rest_url
    server.rest_url = 'http://localhost:8080/'

    try:
        with pytest.raises(HTTPError) as e:
            server.repository().fetch('/')
        assert e.value.response.status_code == 404
    finally:
        server.rest_url = rest_url


def test_file_out(server):
    operation = server.operation('Document.GetChild')
    operation.params({'name': 'workspaces'})
    operation.input('/default-domain')
    file_out = operation.execute(file_out='test')
    with open(file_out, 'rb') as f:
        file_content = json.loads(f.read())
        resp_content = operation.execute()
        assert file_content == resp_content
    os.remove(file_out)


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


def test_unauthorized(server):
    credentials = {
        'username': 'ミカエル',
        'password': 'test',
    }
    user = server.users().create(credentials)

    try:
        new_server = Nuxeo(
            base_url=os.environ.get('NXDRIVE_TEST_NUXEO_URL',
                                    'http://localhost:8080/nuxeo'),
            auth=credentials)

        with pytest.raises(Unauthorized):
            new_server.users().create({
                'username': 'another_one',
                'password': 'test'
            })
    finally:
        user.delete()
