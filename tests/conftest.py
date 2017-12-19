# coding: utf-8
from __future__ import print_function

import os
import socket

import pytest
from requests import HTTPError

from nuxeo.blob import BufferBlob
from nuxeo.document import Document
from nuxeo.nuxeo import Nuxeo


def pytest_namespace():
    """
    This namespace is used to store global variables for tests.
    They can be accessed with `pytest.<variable_name>` e.g. `pytest.ws_root_path`
    """
    return {'ws_root_path': '/default-domain/workspaces',
            'ws_python_test_name': 'ws-python-tests',
            'ws_python_tests_path': '/default-domain/workspaces/ws-python-tests',
            }


@pytest.fixture(scope='function', autouse=True)
def cleanup(server, repository):
    try:
        doc = repository.fetch(pytest.ws_root_path)
        params = {'pageProvider': 'CURRENT_DOC_CHILDREN',
                  'queryParams': [doc.uid]}
        docs = repository.query(params)
        for doc in docs['entries']:
            doc.delete()
    except (HTTPError, socket.timeout):
        pass


@pytest.fixture(scope='function')
def doc(server, repository):
    new_doc = {
        'name': pytest.ws_python_test_name,
        'type': 'File',
        'properties': {
            'dc:title': 'bar.txt',
        },
    }
    doc = repository.create(pytest.ws_root_path, new_doc)
    assert doc is not None
    assert isinstance(doc, Document)
    assert doc.path == pytest.ws_python_tests_path
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


@pytest.fixture(scope='function')
def georges(server):
    opts = {
        'lastName': 'Abitbol',
        'firstName': 'Georges',
        'username': 'georges',
        'company': 'Pom Pom Gali resort',
        'password': 'Test'}
    return server.users().create(opts)


@pytest.fixture(scope='module')
def repository(server):
    return server.repository(schemas=['dublincore'])


@pytest.fixture(scope='module')
def server():
    return Nuxeo(base_url=os.environ.get('NXDRIVE_TEST_NUXEO_URL',
                                         'http://localhost:8080/nuxeo'),
                 auth={'username': 'Administrator', 'password': 'Administrator'})
