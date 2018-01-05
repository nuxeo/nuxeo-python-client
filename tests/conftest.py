# coding: utf-8
from __future__ import unicode_literals

import logging
import os
import socket

import pytest
import requests

from nuxeo.client import Nuxeo
from nuxeo.exceptions import HTTPError

logging.basicConfig(format='%(module)-14s %(levelname).1s %(message)s',
                    level=logging.DEBUG)


def pytest_namespace():
    """
    This namespace is used to store global variables for tests.
    They can be accessed with `pytest.<variable_name>` e.g. `pytest.ws_root_path`
    """
    return {
        'ws_root_path': '/default-domain/workspaces',
        'ws_python_test_name': 'ws-python-tests',
        'ws_python_tests_path': '/default-domain/workspaces/ws-python-tests',
    }


@pytest.fixture(scope='function', autouse=True)
def cleanup(server):
    try:
        docs = server.documents.get_children(path=pytest.ws_root_path)
        for doc in docs:
            doc.delete()
    except (HTTPError, socket.timeout):
        pass


@pytest.fixture(scope='module')
def directory(server):
    directory = server.directories.get('nature')
    try:
        directory.delete('foo')
    except HTTPError:
        pass
    return directory


@pytest.fixture(scope='module')
def repository(server):
    return server.documents


@pytest.fixture(scope='module')
def server():
    assert requests.__version__ >= '2.12.2'
    server = Nuxeo(host=os.environ.get('NXDRIVE_TEST_NUXEO_URL',
                                       'http://localhost:8080/nuxeo'),
                   auth=('Administrator', 'Administrator'))
    server.client.set(schemas=['dublincore'])
    return server
