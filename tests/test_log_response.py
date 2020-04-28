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


class ResponseEmpty(Response):
    def __init__(self):
        super().__init__()
        self.url = "http://localhost:8080/nuxeo/nothing"


class ResponseAutomation(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "application/json"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/site/automation"


class ResponseCmis(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "application/json"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/json/cmis"


class ResponseMov(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "video/quicktime"
        self.headers["content-length"] = 1088996060
        self.url = "http://localhost:8080/nuxeo/1.0%20GiB.mov"

    @property
    def content(self):
        raise MemoryError()


class ResponseIso(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "application/octet-stream"
        self.headers["content-length"] = "734334976"
        self.url = "http://localhost:8080/nuxeo/700.3%20MiB.iso"

    @property
    def content(self):
        raise MemoryError()


class ResponseMxf(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "application/mxf"
        self.headers["content-length"] = "8932294324"
        self.url = "http://localhost:8080/nuxeo/8.3%20GiB.mxf"

    @property
    def content(self):
        raise OverflowError("join() result is too long")


class ResponseChunkedContents(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.headers["transfer-encoding"] = "chunked"
        self.url = "http://localhost:8080/nuxeo/small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseTextOk(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/small%20file.txt"

    @property
    def content(self):
        return "TADA!".encode("utf-8")


class ResponseTextError(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = "1024"
        self.url = "http://localhost:8080/nuxeo/big%20file.txt"

    @property
    def content(self):
        raise MemoryError()


class ResponseTextTooLong(Response):
    def __init__(self):
        super().__init__()
        self.headers["content-type"] = "text/plain"
        self.headers["content-length"] = 4096 * 2
        self.url = "http://localhost:8080/nuxeo/big%20file.txt"


@pytest.mark.parametrize(
    "response, pattern",
    [
        (ResponseEmpty, "no content"),
        (ResponseAutomation, "Automation details"),
        (ResponseCmis, "CMIS details"),
        (ResponseMov, "binary data"),
        (ResponseMxf, "binary data"),
        (ResponseIso, "binary data"),
        (ResponseTextOk, "TADA!"),
        (ResponseTextTooLong, "too much text"),
        (ResponseTextError, "no enough memory"),
        (ResponseChunkedContents, "chunked contents"),
    ],
)
def test_response(caplog, response, pattern):
    """Test all kind of responses to cover the whole method."""
    caplog.clear()
    NuxeoClient._log_response(response(), 4096)

    assert caplog.records
    for record in caplog.records:
        assert record.levelname == "DEBUG"
        assert pattern in record.message


def test_response_with_logger_not_in_debug(caplog):
    """If the logging level is higher than DEBUG, nothing is logged."""
    with caplog.at_level(logging.INFO):
        NuxeoClient._log_response(ResponseEmpty(), 4096)
    assert not caplog.records
