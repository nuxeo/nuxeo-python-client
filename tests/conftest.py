# coding: utf-8
from __future__ import unicode_literals

import logging

import os
import pytest
from requests.cookies import RequestsCookieJar

from nuxeo.client import Nuxeo
from nuxeo.exceptions import HTTPError

logging.basicConfig(
    format="%(module)-14s %(levelname).1s %(message)s", level=logging.DEBUG
)


@pytest.fixture(scope="function", autouse=True)
def server_log(request, server):
    msg = ">>> testing: {}.{}".format(
        request.module.__name__, request.function.__name__
    )
    server.operations.execute(command="Log", level="warn", message=msg)


@pytest.fixture(scope="module")
def directory(server):
    directory = server.directories.get("nature")
    try:
        directory.delete("foo")
    except HTTPError:
        pass
    return directory


@pytest.fixture(scope="module")
def repository(server):
    return server.documents


@pytest.fixture(scope="module")
def server():
    cookies = RequestsCookieJar()
    cookies.set("device", "python-client")
    server = Nuxeo(
        host=os.environ.get("NXDRIVE_TEST_NUXEO_URL", "http://localhost:8080/nuxeo"),
        auth=("Administrator", "Administrator"),
        cookies=cookies,
    )
    server.client.set(schemas=["dublincore"])

    # We do not need the retry feature in tests as it breaks too many uploads tests.
    # But we will test that particular feature in one specific test.
    server.client.disable_retry()

    return server


@pytest.fixture(scope="function")
def retry_server(server):
    server.client.enable_retry()
    yield server
    server.client.disable_retry()
