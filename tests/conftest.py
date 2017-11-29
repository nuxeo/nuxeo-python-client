# coding: utf-8

from __future__ import print_function

import os
import socket
from urllib2 import HTTPError

import pytest

from nuxeo.blob import BufferBlob
from nuxeo.document import Document
from nuxeo.nuxeo import Nuxeo

WS_ROOT_PATH = '/default-domain/workspaces'
WS_PYTHON_TEST_NAME = 'ws-python-tests'
WS_PYTHON_TESTS_PATH = WS_ROOT_PATH + '/' + WS_PYTHON_TEST_NAME

base_url = os.environ.get('NXDRIVE_TEST_NUXEO_URL', 'http://localhost:8080/nuxeo')
auth = {'username': 'Administrator', 'password': 'Administrator'}


@pytest.fixture(scope='function')
def clean_root(repository):
    try:
        repository.fetch(WS_PYTHON_TESTS_PATH).delete()
    except (HTTPError, socket.timeout):
        pass


@pytest.fixture(scope='function')
def create_blob_file(server, repository):
    new_doc = {
        'name': WS_PYTHON_TEST_NAME,
        'type': 'File',
        'properties': {
            'dc:title': 'bar.txt',
        },
    }
    doc = repository.create(WS_ROOT_PATH, new_doc)
    assert doc is not None
    assert isinstance(doc, Document)
    assert doc.path == WS_PYTHON_TESTS_PATH
    assert doc.type == 'File'
    assert doc.properties['dc:title'] == 'bar.txt'

    blob = BufferBlob('foo', 'foo.txt', 'text/plain')
    blob = server.batch_upload().upload(blob)
    doc.properties['file:content'] = blob
    doc.save()
    return doc


@pytest.fixture(scope='module')
def directory(server):
    directory = server.directory('nature')
    try:
        directory.fetch('foo').delete()
    except HTTPError:
        pass
    return directory


@pytest.fixture(scope='module')
def repository(server):
    return server.repository(schemas=['dublincore'])


@pytest.fixture(scope='module')
def server(request):
    return Nuxeo(base_url=base_url, auth=auth)
