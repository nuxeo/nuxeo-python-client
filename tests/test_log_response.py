# coding: utf-8
"""
Test log_response() to prevent regressions causing memory errors.
requests Responses objects are crafted based on real usecases that broke something at some point.
"""
import logging
from unittest.mock import patch

import pytest
from requests import HTTPError, Response
from nuxeo.client import NuxeoClient
from nuxeo.utils import log_response
from .constants import NUXEO_SERVER_URL

nuxeo_url = NUXEO_SERVER_URL

# We do not need to set-up a server and log the current test
skip_logging = True


class ResponseAutomation(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json"
        self.headers["content-length"] = "1024"
        self.url = f"{nuxeo_url}site/automation"


class ResponseChunkedContents(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["transfer-encoding"] = "chunked"
        self.url = f"{nuxeo_url}small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseChunkedJsonContents(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json; nuxeo-entity=document"
        self.headers["transfer-encoding"] = "chunked"
        self.url = f"{nuxeo_url}small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseChunkedJsonContentsTooLong(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json; nuxeo-entity=document"
        self.headers["transfer-encoding"] = "chunked"
        self.url = f"{nuxeo_url}small%20file.txt"

    @property
    def content(self):
        return ("TADA!" * 4096 * 2).encode("utf-8")


class ResponseCmis(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json"
        self.headers["content-length"] = "1024"
        self.url = f"{nuxeo_url}json/cmis"


class ResponseEmpty(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json"
        self.url = f"{nuxeo_url}nothing"

    @property
    def content(self):
        return b""


class ResponseError409(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 409
        self.headers["content-type"] = "application/json"
        self.headers["transfer-encoding"] = "chunked"
        self.url = f"{nuxeo_url}nothing"

    @property
    def content(self):
        return (
            b'{"entity-type":"exception","status":409,"message":"Failed to delete document '
            b"/default-domain/workspaces/ws-python-tests, Failed to remove document "
            b'6a502942-f83b-4742-bb0c-132905ee88bf, Concurrent update"}'
        )


class ResponseError500Empty(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 500

    @property
    def content(self):
        return b"foo"


class ResponseError500EmptyMessage(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 500
        self.reason = "Erreur Interne de Servlet"

    @property
    def content(self):
        return b'{"message":""}'


class ResponseError500WithReason(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 500
        self.reason = "Erreur Interne de Servlet"

    @property
    def content(self):
        return b'{"stacktrace": "my error"}'


class ResponseIso(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/octet-stream"
        self.headers["content-length"] = "734334976"
        self.url = f"{nuxeo_url}700.3%20MiB.iso"

    @property
    def content(self):
        raise MemoryError()


class ResponseMov(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "video/quicktime"
        self.headers["content-length"] = 1088996060
        self.url = f"{nuxeo_url}1.0%20GiB.mov"

    @property
    def content(self):
        raise MemoryError()


class ResponseMxf(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/mxf"
        self.headers["content-length"] = "8932294324"
        self.url = f"{nuxeo_url}8.3%20GiB.mxf"

    @property
    def content(self):
        raise OverflowError("join() result is too long")


class ResponseTextError(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.url = f"{nuxeo_url}big%20file.txt"

    @property
    def content(self):
        raise MemoryError()


class ResponseTextOk(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.url = f"{nuxeo_url}small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseTextTooLong(Response):
    def __init__(self):
        super().__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = 4096 * 2
        self.url = f"{nuxeo_url}big%20file.txt"

    @property
    def content(self):
        return ("TADA!" * 4096 * 2).encode("utf-8")


@pytest.mark.parametrize(
    "response, pattern",
    [
        (ResponseAutomation, "Automation details"),
        (ResponseEmpty, "no content"),
        (ResponseError409, "Concurrent update"),
        (ResponseChunkedContents, "TADA!"),
        (ResponseChunkedJsonContents, "TADA!"),
        (ResponseChunkedJsonContentsTooLong, " [...] "),
        (ResponseCmis, "CMIS details"),
        (ResponseIso, "binary data"),
        (ResponseMov, "binary data"),
        (ResponseMxf, "binary data"),
        (ResponseTextError, "no enough memory"),
        (ResponseTextOk, "TADA!"),
        (ResponseTextTooLong, " [...] "),
    ],
)
@patch("nuxeo.constants.LOG_LIMIT_SIZE", 4096)
def test_response(caplog, response, pattern):
    """Test all kind of responses to cover the whole method."""
    caplog.clear()
    log_response(response())

    assert caplog.records
    for record in caplog.records:
        assert record.levelname == "DEBUG"
        assert pattern in record.message


def test_response_long(caplog):
    """Test a long response that is not truncated."""
    caplog.clear()
    log_response(ResponseTextTooLong())

    assert caplog.records
    for record in caplog.records:
        assert record.levelname == "DEBUG"
        assert " [...] " not in record.message


def test_response_with_logger_not_in_debug(caplog):
    """If the logging level is higher than DEBUG, nothing is logged."""
    with caplog.at_level(logging.INFO):
        log_response(ResponseEmpty())
    assert not caplog.records


def test_500_empty_content():
    response = ResponseError500Empty()
    exception = HTTPError(response=response)
    error = NuxeoClient._handle_error(exception)
    assert error.status == 500
    assert error.message == b"foo"


def test_500_empty_message():
    response = ResponseError500EmptyMessage()
    exception = HTTPError(response=response)
    error = NuxeoClient._handle_error(exception)
    assert error.status == 500
    assert error.message == "Erreur Interne de Servlet"


def test_500_with_reason():
    response = ResponseError500WithReason()
    exception = HTTPError(response=response)
    error = NuxeoClient._handle_error(exception)
    assert error.status == 500
    assert error.message == "Erreur Interne de Servlet"
    assert error.stacktrace == "my error"
