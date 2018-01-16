# coding: utf-8
from __future__ import unicode_literals

import json
import sys

import os
import pkg_resources
import pytest
import re
import requests
from requests.exceptions import ConnectionError

from nuxeo import _extract_version
from nuxeo.compat import get_bytes
from nuxeo.exceptions import HTTPError, Unauthorized
from nuxeo.models import Blob, User


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
        server.operations.check_params(method, params)
    else:
        with pytest.raises(TypeError):
            server.operations.check_params(method, params)


def test_check_params_unknown_operation(server):
    with pytest.raises(ValueError):
        server.operations.check_params('alien', {})


def test_check_params_unknown_param(server):
    with pytest.raises(ValueError):
        server.operations.check_params(
            'Document.Query', {'alien': 'alien'})


def test_encoding_404_error(server):
    url = server.client.host
    server.client.host = 'http://localhost:8080/'

    try:
        with pytest.raises((ConnectionError, HTTPError)) as e:
            server.documents.get(path='/')
        if isinstance(e, HTTPError):
            assert e.value.status == 404
    finally:
        server.client.host = url


def test_file_out(server):
    operation = server.operations.new('Document.GetChild')
    operation.params = {'name': 'workspaces'}
    operation.input_obj = '/default-domain'
    file_out = operation.execute(file_out='test')
    with open(file_out, 'rb') as f:
        file_content = json.loads(f.read())
        resp_content = operation.execute()
        assert file_content == resp_content
    os.remove(file_out)


def test_get_operations(server):
    assert server.operations


def test_init(monkeypatch):
    def missing_dist(_):
        raise pkg_resources.DistributionNotFound

    assert re.match('\d+\.\d+\.\d+', _extract_version())
    monkeypatch.setattr(pkg_resources, 'get_distribution', missing_dist)
    assert re.match('\d+\.\d+\.\d+', _extract_version())


def test_request_token(server):
    app_name = 'Nuxeo Drive'
    device_id = '41f0711a-f008-4c11-b3f1-c5bddcb50d77'
    device_descr = {
        'cygwin': 'Windows',
        'darwin': 'macOS',
        'linux2': 'GNU/Linux',
        'win32': 'Windows',
    }.get(sys.platform)
    permission = 'ReadWrite'

    prev_auth = server.client.auth

    token = server.client.request_auth_token(device_id, permission, app_name, device_descr)
    assert server.client.auth.token == token
    assert server.client.is_reachable()
    server.client.auth = prev_auth


def test_send_wrong_method(server):
    with pytest.raises(ValueError):
        server.client.request('TEST', 'example')


def test_server_reachable(server):
    assert server.client.is_reachable()
    url = server.client.host
    server.client.host = 'http://example.org'

    try:
        assert not server.client.is_reachable()
    finally:
        server.client.host = url


@pytest.mark.skipif(
    requests.__version__ < '2.12.2',
    reason='Requests >= 2.12.2 required for auth unicode support.')
def test_unauthorized(server):
    username = 'ミカエル'
    password = 'test'
    user = server.users.create(
        User(properties={
            'username': username,
            'password': password
        }))

    auth = server.client.auth
    server.client.auth = (get_bytes(username), password)
    try:

        with pytest.raises(Unauthorized):
            server.users.create(
                User(properties={
                    'username': 'another_one',
                    'password': 'test'
                }))
    finally:
        server.client.auth = auth
        user.delete()
