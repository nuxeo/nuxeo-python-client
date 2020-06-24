# coding: utf-8
"""
Test NuxeoClient._log_response() to prevent regressions causing memory errors.
requests Responses objects are crafted based on real usecases that broke something at some point.
"""
import logging

import pytest
from requests import Response
from nuxeo.client import NuxeoClient


# We do not need to set-up a server and log the current test
skip_logging = True


class ResponseAutomation(Response):
    def __init__(self):
        # super() will be used when Python 2 support will be dropped (NXPY-129)
        super(ResponseAutomation, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/site/automation"


class ResponseChunkedContents(Response):
    def __init__(self):
        super(ResponseChunkedContents, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["transfer-encoding"] = "chunked"
        self.url = "http://localhost:8080/nuxeo/small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseChunkedJsonContents(Response):
    def __init__(self):
        super(ResponseChunkedJsonContents, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json; nuxeo-entity=document"
        self.headers["transfer-encoding"] = "chunked"
        self.url = "http://localhost:8080/nuxeo/small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseChunkedJsonContentsTooLong(Response):
    def __init__(self):
        super(ResponseChunkedJsonContentsTooLong, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json; nuxeo-entity=document"
        self.headers["transfer-encoding"] = "chunked"
        self.url = "http://localhost:8080/nuxeo/small%20file.txt"

    @property
    def content(self):
        return ("TADA!" * 4096 * 2).encode("utf-8")


class ResponseCmis(Response):
    def __init__(self):
        super(ResponseCmis, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/json/cmis"


class ResponseEmpty(Response):
    def __init__(self):
        super(ResponseEmpty, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/json"
        self.url = "http://localhost:8080/nuxeo/nothing"

    @property
    def content(self):
        return b""


class ResponseError409(Response):
    def __init__(self):
        super(ResponseError409, self).__init__()
        self.status_code = 409
        self.headers["content-type"] = "application/json"
        self.headers["transfer-encoding"] = "chunked"
        self.url = "http://localhost:8080/nuxeo/nothing"

    @property
    def content(self):
        return (
            b'{"entity-type":"exception","status":409,"message":"Failed to delete document '
            b"/default-domain/workspaces/ws-python-tests, Failed to remove document "
            b'6a502942-f83b-4742-bb0c-132905ee88bf, Concurrent update"}'
        )


class ResponseIso(Response):
    def __init__(self):
        super(ResponseIso, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/octet-stream"
        self.headers["content-length"] = "734334976"
        self.url = "http://localhost:8080/nuxeo/700.3%20MiB.iso"

    @property
    def content(self):
        raise MemoryError()


class ResponseMov(Response):
    def __init__(self):
        super(ResponseMov, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "video/quicktime"
        self.headers["content-length"] = 1088996060
        self.url = "http://localhost:8080/nuxeo/1.0%20GiB.mov"

    @property
    def content(self):
        raise MemoryError()


class ResponseMxf(Response):
    def __init__(self):
        super(ResponseMxf, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "application/mxf"
        self.headers["content-length"] = "8932294324"
        self.url = "http://localhost:8080/nuxeo/8.3%20GiB.mxf"

    @property
    def content(self):
        raise OverflowError("join() result is too long")


class ResponseTextError(Response):
    def __init__(self):
        super(ResponseTextError, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/big%20file.txt"

    @property
    def content(self):
        raise MemoryError()


class ResponseTextOk(Response):
    def __init__(self):
        super(ResponseTextOk, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseTextTooLong(Response):
    def __init__(self):
        super(ResponseTextTooLong, self).__init__()
        self.status_code = 200
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = 4096 * 2
        self.url = "http://localhost:8080/nuxeo/big%20file.txt"

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
def test_response(caplog, response, pattern):
    """Test all kind of responses to cover the whole method."""
    caplog.clear()
    NuxeoClient._log_response(response(), limit_size=4096)

    assert caplog.records
    for record in caplog.records:
        assert record.levelname == "DEBUG"
        assert pattern in record.message


def test_response_long(caplog):
    """Test a long response that is not truncated."""
    caplog.clear()
    NuxeoClient._log_response(ResponseTextTooLong())

    assert caplog.records
    for record in caplog.records:
        assert record.levelname == "DEBUG"
        assert " [...] " not in record.message


def test_response_with_logger_not_in_debug(caplog):
    """If the logging level is higher than DEBUG, nothing is logged."""
    with caplog.at_level(logging.INFO):
        NuxeoClient._log_response(ResponseEmpty(), 4096)
    assert not caplog.records
