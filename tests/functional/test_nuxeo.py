# coding: utf-8
import json
import logging
from unittest.mock import patch

import pytest
import requests
import responses
from nuxeo import constants
from nuxeo.constants import MAX_RETRY, RETRY_METHODS
from nuxeo.endpoint import APIEndpoint
from nuxeo.exceptions import BadQuery, Forbidden, HTTPError, Unauthorized
from nuxeo.models import Blob, User
from requests.exceptions import ConnectionError
from ..constants import SSL_VERIFY


@pytest.mark.parametrize(
    "method, params, is_valid",
    [
        # 'file' type in (Blob, str)
        ("Document.SetBlob", {"file": Blob()}, True),
        ("Document.SetBlob", {"file": "test.txt"}, True),
        ("Document.SetBlob", {"file": 0}, False),
        # 'blockInheritance' type == boolean
        (
            "Document.AddPermission",
            {"permission": "Read", "blockInheritance": False},
            True,
        ),
        (
            "Document.AddPermission",
            {"permission": "Read", "blockInheritance": "false"},
            False,
        ),
        # 'end' type == str
        ("Document.AddPermission", {"permission": "Read", "end": "01-01-2018"}, True),
        ("Document.AddPermission", {"permission": "Read", "end": True}, False),
        # 'value' type == str
        ("Document.Fetch", {"value": "test.txt"}, True),
        ("Document.Fetch", {"value": True}, False),
        # 'target' type == list
        ("Document.MultiPublish", {"target": ["test1.txt", "test2.txt"]}, True),
        ("Document.MultiPublish", {"target": 0}, False),
        # 'pageNo' type == int
        ("Audit.Query", {"query": "test", "pageNo": 100}, True),
        # 'pageSize' type == int
        ("Audit.Query", {"query": "test", "pageNo": "test"}, False),
        ("Document.Query", {"query": "test", "pageSize": 10}, True),
        ("Document.Query", {"query": "test", "pageSize": "test"}, False),
        # 'startPage', 'endPage' type == long
        ("PDF.ExtractPages", {"startPage": 1, "endPage": int(2)}, True),
        ("PDF.ExtractPages", {"startPage": "test", "endPage": "test"}, False),
        # 'info' type == dict
        ("User.Invite", {"info": {"username": "test"}}, True),
        ("User.Invite", {"info": 0}, False),
        # 'properties' type == dict
        (
            "Document.Create",
            {"type": "Document", "properties": {"dc:title": "test"}},
            True,
        ),
        ("Document.Create", {"type": "Document", "properties": 0}, False),
        # 'file' type == str
        ("Blob.Create", {"file": "test.txt"}, True),
        ("Blob.Create", {"file": 0}, False),
        # 'value' type == Sequence
        ("Document.SetProperty", {"xpath": "test", "value": "test"}, True),
        ("Document.SetProperty", {"xpath": "test", "value": [0, 1, 2]}, True),
        ("Document.SetProperty", {"xpath": "test", "value": 0}, False),
        # 'query' type == str
        ("Document.Query", {"query": "test"}, True),
        ("Document.Query", {"query": 0}, False),
        # 'queryParams' type in [list, str]
        ("Document.Query", {"query": "test", "queryParams": ["a", "b", "c"]}, True),
        ("Document.Query", {"query": "test", "queryParams": "test"}, True),
        ("Document.Query", {"query": "test", "queryParams": 0}, False),
        # 'queryParams' is also optional, None should be accepted
        ("Document.Query", {"query": "test", "queryParams": None}, True),
        # 'validationMethod' type == str
        ("User.Invite", {"validationMethod": "test"}, True),
        ("User.Invite", {"validationMethod": 0}, False),
        # unknown param
        ("Document.Query", {"alien": "alien"}, False),
    ],
)
def test_check_params(method, params, is_valid, server):
    if is_valid:
        try:
            server.operations.check_params(method, params)
        except Exception as e:
            print(f">>>> Exception: {e!r}")
            assert 1 == 0
    else:
        with pytest.raises(BadQuery):
            server.operations.check_params(method, params)


def test_check_params_constant(server):
    operation = server.operations.new("Document.GetChild")
    operation.params = {"name": "workspaces", "alien": "the return"}
    operation.input_obj = "/default-domain"

    # Should not fail here
    assert not constants.CHECK_PARAMS
    operation.execute()

    # But should fail now
    with patch.object(constants, "CHECK_PARAMS", new=True):
        with pytest.raises(BadQuery):
            operation.execute()


def test_check_params_unknown_operation(server):
    with pytest.raises(BadQuery):
        server.operations.check_params("alien", {})


def test_encoding_404_error(server):
    with patch.object(server.client, "host", new="http://localhost:8080/"):
        with pytest.raises((ConnectionError, HTTPError)) as e:
            server.documents.get(path="/")
        if isinstance(e, HTTPError):
            assert e.value.status == 404


def test_handle_error(server):
    err = ValueError("test")
    err_handled = server.client._handle_error(err)
    assert err == err_handled


def test_file_out(tmp_path, server):
    operation = server.operations.new("Document.GetChild")
    operation.params = {"name": "workspaces"}
    operation.input_obj = "/default-domain"

    check_cb = check_lock = check_unlock = 0

    def callback(path):
        nonlocal check_cb
        check_cb += 1

    def unlock_path(path):
        nonlocal check_unlock
        check_unlock += 1
        return True

    def lock_path(path, locker):
        nonlocal check_lock
        check_lock += 1

    file_out = operation.execute(
        file_out=tmp_path / "file_out",
        callback=callback,
        lock_path=lock_path,
        unlock_path=unlock_path,
    )

    with open(file_out) as f:
        file_content = json.loads(f.read())
    resp_content = operation.execute()
    assert file_content == resp_content

    # Check callback and lock/unlock calls are unique
    assert check_cb == 1
    assert check_lock == 1
    assert check_unlock == 1


def test_file_out_several_callbacks(tmp_path, server):
    operation = server.operations.new("Document.GetChild")
    operation.params = {"name": "workspaces"}
    operation.input_obj = "/default-domain"

    check1 = check2 = 0

    def callback1(path):
        nonlocal check1
        check1 += 1

    def callback2(path):
        nonlocal check2
        check2 += 1

    callbacks = (callback1, callback2)
    file_out = operation.execute(file_out=tmp_path / "file_out", callback=callbacks)

    with open(file_out) as f:
        file_content = json.loads(f.read())
    resp_content = operation.execute()
    assert file_content == resp_content

    # Check callbacks calls are unique
    assert check1 == 1
    assert check2 == 1


def test_get_operations(server):
    assert server.operations


def test_operation_default(server):
    operation = server.operations.new("Document.GetChild")
    operation.params = {"name": "workspaces"}
    operation.input_obj = "/default-domain"

    operation.execute(check_params=True, default=0)


def test_operation_command_with_timeout(server):
    with pytest.raises(ConnectionError) as exc:
        server.operations.execute(
            command="Document.Create", type="File", check_params=True, timeout=0.0001
        )
    error = str(exc.value)
    assert "timed out" in error


def test_post_default(server):
    api = APIEndpoint(server.client, "wrong_endpoint")
    res = api.post({}, default={"response": "noerror"})
    assert res == {"response": "noerror"}


def test_query(server):
    search = server.client.query("SELECT * FROM Domain")
    assert search["entries"]


def test_query_empty(server):
    query = 'SELECT * FROM Document WHERE uid = "non-existant-ahah"'
    params = {"properties": "*"}
    search = server.client.query(query, params=params)
    assert not search.get("entries")


@pytest.mark.parametrize("method", RETRY_METHODS)
def test_max_retry(caplog, retry_server, method):
    caplog.set_level(logging.WARNING)
    session = retry_server.client._session

    with pytest.raises(requests.exceptions.ConnectionError):
        if SSL_VERIFY is False:
            session.request(method, "http://example.42.org", verify=SSL_VERIFY)
        else:
            session.request(method, "http://example.42.org")

    for retry_number, record in enumerate(caplog.records, 1):
        assert record.levelname == "WARNING"
        text = f"Retrying (Retry(total={MAX_RETRY - retry_number}"
        assert text in record.message


def test_server_info(server):
    server.client._server_info = None
    server_info = server.client.server_info

    # First call
    assert server_info()
    assert isinstance(server_info(), dict)

    # Force the call
    server.client._server_info = None
    assert server_info() is server_info()
    assert server_info() is not server_info(force=True)

    # If the sentinel value is not None, then the call should _not_ be made to the server
    info = server_info()
    server.client._server_info = {}
    assert server_info() is not info
    assert server_info() == {}

    # Bad call
    server.client._server_info = None
    with patch.object(server.client, "host", new="http://example-42.org/"):
        assert not server_info()


def test_server_info_bad_response(server):
    """
    Test bad response data (not serializable JSON).
    NXPY-171: the call should not fail.
    """
    server_info = server.client.server_info

    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{server.client.host}json/cmis", body="...")
        assert server_info(force=True) is None

    # Another call, it must work as expected
    assert server_info(force=True) is not None


def test_server_version(server):
    server.client._server_info = None
    assert server.client.server_version
    assert str(server.client)


def test_server_version_bad_url(server):
    server.client._server_info = None
    with patch.object(server.client, "host", new="http://example-42.org/"):
        assert server.client.server_version == "unknown"
        assert str(server.client)

    # Another call, it must work as expected
    assert server.client.server_version != "unknown"
    assert str(server.client)


def test_server_version_bad_response_from_server_info(server):
    """
    Test bad response data (not serializable JSON).
    NXPY-177: the call should not fail on an AttributeError.
    """
    server.client._server_info = None
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, f"{server.client.host}json/cmis", body="...")
        assert server.client.server_version == "unknown"

    # Another call, it must work as expected
    assert server.client.server_version != "unknown"


def test_set_repository(server):
    server.client.set(repository="foo")
    assert server.documents._path(uid="1234") == "repo/foo/id/1234"
    server.client.set(repository="default")


def test_request_token(server):
    app_name = "Nuxeo Drive"
    device_id = "41f0711a-f008-4c11-b3f1-c5bddcb50d77"
    device = "GNU/Linux"
    permission = "ReadWrite"

    prev_auth = server.client.auth
    try:
        token = server.client.request_auth_token(
            device_id,
            permission,
            app_name=app_name,
            device=device,
            ssl_verify=SSL_VERIFY,
        )
        assert server.users.current_user(ssl_verify=SSL_VERIFY)

        # Calling twice should return the same token
        same_token = server.client.request_auth_token(
            device_id, permission, app_name=app_name, device=device
        )
        assert token == same_token
    finally:
        server.client.auth = prev_auth


def test_send_wrong_method(server):
    with pytest.raises(BadQuery):
        server.client.request("TEST", "example", ssl_verify=SSL_VERIFY)


def test_server_reachable(server):
    assert server.client.is_reachable()
    with patch.object(server.client, "host", new="http://example.org"):
        assert not server.client.is_reachable()
    assert server.client.is_reachable()


@pytest.mark.skipif(
    requests.__version__ < "2.12.2",
    reason="Requests >= 2.12.2 required for auth unicode support.",
)
def test_forbidden(server):
    username = "ミカエル"
    password = "test"
    user = server.users.create(
        User(properties={"username": username, "password": password})
    )

    auth = server.client.auth
    server.client.auth = (username.encode("utf-8"), password)
    try:
        with pytest.raises(Forbidden) as e:
            server.users.create(
                User(properties={"username": "another_one", "password": "test"})
            )
        assert str(e.value).startswith("Forbidden(403)")
    finally:
        server.client.auth = auth
        user.delete()


def test_unauthorized(server):
    username = "alice"
    password = "test"
    auth = server.client.auth
    server.client.auth = (username.encode("utf-8"), password)
    try:
        with pytest.raises(Unauthorized) as e:
            server.users.create(
                User(properties={"username": "another_one", "password": "test"})
            )
        assert str(e.value).startswith("Unauthorized(401)")
    finally:
        server.client.auth = auth


def test_param_format(server, recwarn):
    params = "stringnotadict"
    with pytest.raises(HTTPError):
        server.client.request("GET", "test", params=params, ssl_verify=SSL_VERIFY)

    if (
        SSL_VERIFY is False
        and recwarn
        and "Adding certificate verification is strongly advised" in str(recwarn[0])
    ):
        recwarn.pop()

    assert len(recwarn) == 0

    params = {"test.wrong.typo": "error"}
    with pytest.warns(
        DeprecationWarning,
        match=r"'test.wrong.typo' param should not contain '_' nor '.'. Replace with '-' "
        r"to get rid of that warning.",
    ):
        with pytest.raises(HTTPError):
            server.client.request("GET", "test", params=params, ssl_verify=SSL_VERIFY)


def test_header_format(server):
    with pytest.warns(
        DeprecationWarning,
        match=r"'test.wrong.typo' header should not contain '_' nor '.'. Replace with '-' "
        r"to get rid of that warning.",
    ):
        with pytest.raises(HTTPError):
            headers = {"test.wrong.typo": "error"}
            server.client.request("GET", "test", headers=headers, ssl_verify=SSL_VERIFY)


def test_can_use(server):
    assert server.can_use("FileManager.Import")
    assert not server.can_use("FileManager.ImportAndKillTheServer")
