from nuxeo.exceptions import (
    Conflict,
    Forbidden,
    HTTPError,
    OngoingRequestError,
    Unauthorized,
)


# We do not need to set-up a server and log the current test
skip_logging = True


def test_crafted_conflict():
    exc = Conflict()
    assert exc.status == 409


def test_crafted_forbidden():
    exc = Forbidden()
    assert exc.status == 403


def test_crafted_httperror():
    exc = HTTPError()
    assert exc.status == -1
    assert exc.message is None
    assert exc.stacktrace is None


def test_crafted_httperror_with_message():
    exc = HTTPError(message="oups")
    assert exc.status == -1
    assert exc.message == "oups"
    assert exc.stacktrace is None


def test_crafted_httperror_with_message_and_stacktrace():
    exc = HTTPError(message="oups", stacktrace="NulPointerException: bla*3")
    assert exc.status == -1
    assert exc.message == "oups"
    assert exc.stacktrace == "NulPointerException: bla*3"


def test_crafted_httperror_parse():
    cls = HTTPError()
    exc = cls.parse({"message": "oups", "stacktrace": "NulPointerException: bla*3"})
    assert exc.status == -1
    assert exc.message == "oups"
    assert exc.stacktrace == "NulPointerException: bla*3"


def test_crafted_ongoing_request_error():
    exc = OngoingRequestError("123-456-789")
    assert str(exc)
    assert exc.status == 409
    assert exc.request_uid == "123-456-789"


def test_crafted_unauthorized():
    exc = Unauthorized()
    assert exc.status == 401
