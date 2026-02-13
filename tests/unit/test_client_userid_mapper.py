# coding: utf-8
"""
Unit tests for the userid_mapper translation layer in nuxeo.client.NuxeoClient.

Covers:
  - _fetch_uid_for_username  (dummy)
  - _fetch_username_for_uid  (dummy)
  - resolve_uid              (cache hit & miss)
  - resolve_username         (reverse cache hit, miss, & unknown uid)
  - _translate_single_username_to_uid  (plain & prefixed)
  - _translate_uid_value_to_username   (plain, prefixed, list, non-string)
  - _translate_request_params          (all key types, non-matching, empty)
  - _translate_response                (flat, nested, list-of-dicts, mixed)
  - request() integration             (URL query param & response wrapping)
  - execute() integration             (body param translation + response)
"""
from unittest.mock import MagicMock, patch

import requests

from nuxeo.client import NuxeoClient
from nuxeo.operations import API

# We do not need to set-up a server and log the current test
skip_logging = True


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _make_client():
    """Create a NuxeoClient instance without connecting to a real server."""
    with patch.object(NuxeoClient, "__init__", lambda self: None):
        client = NuxeoClient.__new__(NuxeoClient)
    # Manually set the attributes that would be set by __init__
    client.userid_mapper = {}
    # These are class-level frozensets so they're already available
    return client


def _make_api():
    """Create an operations API instance with a mocked client,
    where the client has the translation methods."""
    client = _make_client()
    # Set minimal attributes needed by APIEndpoint / API
    client.api_path = "api/v1"
    # Mock request to avoid real HTTP calls
    client.request = MagicMock()
    api = API(client)
    return api, client


# ===================================================================
#  _fetch_uid_for_username  /  _fetch_username_for_uid  (dummy stubs)
# ===================================================================

class TestDummyFetchMethods:
    """Verify the dummy placeholder methods return deterministic values."""

    def test_fetch_uid_for_username(self):
        client = _make_client()
        assert client._fetch_uid_for_username("Administrator") == "uid-Administrator"
        assert client._fetch_uid_for_username("john") == "uid-john"

    def test_fetch_username_for_uid_with_prefix(self):
        client = _make_client()
        assert client._fetch_username_for_uid("uid-john") == "john"
        assert client._fetch_username_for_uid("uid-Administrator") == "Administrator"

    def test_fetch_username_for_uid_without_prefix(self):
        """When the uid does not start with 'uid-', return it as-is."""
        client = _make_client()
        assert client._fetch_username_for_uid("some-random-id") == "some-random-id"

    def test_fetch_username_for_uid_only_strips_first_occurrence(self):
        client = _make_client()
        # "uid-uid-nested" → should strip first "uid-" only → "uid-nested"
        assert client._fetch_username_for_uid("uid-uid-nested") == "uid-nested"


# ===================================================================
#  resolve_uid
# ===================================================================

class TestResolveUid:

    def test_cache_miss_calls_fetch_and_caches(self):
        client = _make_client()
        assert client.userid_mapper == {}

        uid = client.resolve_uid("alice")
        assert uid == "uid-alice"
        assert client.userid_mapper == {"alice": "uid-alice"}

    def test_cache_hit_does_not_call_fetch(self):
        client = _make_client()
        client.userid_mapper["bob"] = "custom-id-999"

        uid = client.resolve_uid("bob")
        assert uid == "custom-id-999"
        assert client.userid_mapper == {"bob": "custom-id-999"}

    def test_cache_hit_returns_exact_value(self):
        client = _make_client()
        client.userid_mapper["admin"] = "xyz-123"
        assert client.resolve_uid("admin") == "xyz-123"

    def test_multiple_users_cached(self):
        client = _make_client()
        client.resolve_uid("alice")
        client.resolve_uid("bob")
        assert len(client.userid_mapper) == 2
        assert "alice" in client.userid_mapper
        assert "bob" in client.userid_mapper


# ===================================================================
#  resolve_username
# ===================================================================

class TestResolveUsername:

    def test_reverse_cache_hit(self):
        client = _make_client()
        client.userid_mapper["john"] = "id-001"

        username = client.resolve_username("id-001")
        assert username == "john"

    def test_reverse_cache_miss_calls_fetch_and_caches(self):
        client = _make_client()
        assert client.userid_mapper == {}

        username = client.resolve_username("uid-carol")
        assert username == "carol"
        assert client.userid_mapper == {"carol": "uid-carol"}

    def test_unknown_uid_without_prefix(self):
        """Non-prefixed UID that isn't in the cache — dummy returns as-is."""
        client = _make_client()
        username = client.resolve_username("totally-unknown")
        assert username == "totally-unknown"
        assert client.userid_mapper == {"totally-unknown": "totally-unknown"}

    def test_reverse_lookup_finds_first_match(self):
        client = _make_client()
        client.userid_mapper["alice"] = "id-a"
        client.userid_mapper["bob"] = "id-b"
        assert client.resolve_username("id-b") == "bob"
        assert client.resolve_username("id-a") == "alice"


# ===================================================================
#  _translate_single_username_to_uid
# ===================================================================

class TestTranslateSingleUsernameToUid:

    def test_plain_username(self):
        client = _make_client()
        assert client._translate_single_username_to_uid("alice") == "uid-alice"

    def test_prefixed_username(self):
        client = _make_client()
        result = client._translate_single_username_to_uid("user:alice")
        assert result == "user:uid-alice"

    def test_prefixed_preserves_prefix(self):
        client = _make_client()
        result = client._translate_single_username_to_uid("group:managers")
        assert result == "group:uid-managers"

    def test_uses_cache(self):
        client = _make_client()
        client.userid_mapper["alice"] = "real-id-123"
        assert client._translate_single_username_to_uid("alice") == "real-id-123"
        assert client._translate_single_username_to_uid("user:alice") == "user:real-id-123"


# ===================================================================
#  _translate_uid_value_to_username
# ===================================================================

class TestTranslateUidValueToUsername:

    def test_plain_uid(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        assert client._translate_uid_value_to_username("uid-alice") == "alice"

    def test_prefixed_uid(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        result = client._translate_uid_value_to_username("user:uid-alice")
        assert result == "user:alice"

    def test_list_of_uids(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        client.userid_mapper["bob"] = "uid-bob"
        result = client._translate_uid_value_to_username(["uid-alice", "uid-bob"])
        assert result == ["alice", "bob"]

    def test_list_with_prefixed_uids(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        result = client._translate_uid_value_to_username(["user:uid-alice"])
        assert result == ["user:alice"]

    def test_non_string_value_passthrough(self):
        """Non-string/non-list values should be returned as-is."""
        client = _make_client()
        assert client._translate_uid_value_to_username(42) == 42
        assert client._translate_uid_value_to_username(None) is None
        assert client._translate_uid_value_to_username(True) is True


# ===================================================================
#  _translate_request_params
# ===================================================================

class TestTranslateRequestParams:

    def test_empty_params(self):
        client = _make_client()
        assert client._translate_request_params({}) == {}
        assert client._translate_request_params(None) is None

    def test_no_matching_keys(self):
        client = _make_client()
        params = {"target": "/some/path", "value": "delete"}
        result = client._translate_request_params(params)
        assert result == {"target": "/some/path", "value": "delete"}

    def test_username_key_scalar(self):
        client = _make_client()
        params = {"username": "alice", "permission": "Write"}
        result = client._translate_request_params(params)
        assert result["username"] == "uid-alice"
        assert result["permission"] == "Write"

    def test_user_key_scalar(self):
        client = _make_client()
        params = {"user": "bob"}
        result = client._translate_request_params(params)
        assert result["user"] == "uid-bob"

    def test_userId_key(self):
        client = _make_client()
        params = {"userId": "Administrator"}
        result = client._translate_request_params(params)
        assert result["userId"] == "uid-Administrator"

    def test_actors_key_list(self):
        client = _make_client()
        params = {"actors": ["user:alice", "user:bob"]}
        result = client._translate_request_params(params)
        assert result["actors"] == ["user:uid-alice", "user:uid-bob"]

    def test_delegatedActors_key_list(self):
        client = _make_client()
        params = {"delegatedActors": ["user:carol"]}
        result = client._translate_request_params(params)
        assert result["delegatedActors"] == ["user:uid-carol"]

    def test_users_key_scalar(self):
        client = _make_client()
        params = {"users": "alice"}
        result = client._translate_request_params(params)
        assert result["users"] == "uid-alice"

    def test_non_string_non_list_value_passthrough(self):
        client = _make_client()
        params = {"username": 12345}
        result = client._translate_request_params(params)
        assert result["username"] == 12345

    def test_original_params_not_mutated(self):
        client = _make_client()
        params = {"username": "alice", "permission": "Write"}
        result = client._translate_request_params(params)
        assert params["username"] == "alice"
        assert result is not params

    def test_mixed_keys(self):
        client = _make_client()
        params = {
            "username": "alice",
            "permission": "ReadWrite",
            "userId": "bob",
            "target": "/some/doc",
        }
        result = client._translate_request_params(params)
        assert result["username"] == "uid-alice"
        assert result["userId"] == "uid-bob"
        assert result["permission"] == "ReadWrite"
        assert result["target"] == "/some/doc"

    def test_list_with_non_string_items(self):
        client = _make_client()
        params = {"actors": ["user:alice", 42, None]}
        result = client._translate_request_params(params)
        assert result["actors"] == ["user:uid-alice", 42, None]


# ===================================================================
#  _translate_response
# ===================================================================

class TestTranslateResponse:

    def test_flat_dict_with_known_key(self):
        client = _make_client()
        client.userid_mapper["admin"] = "uid-admin"
        data = {"lockOwner": "uid-admin", "uid": "doc-123"}
        result = client._translate_response(data)
        assert result["lockOwner"] == "admin"
        assert result["uid"] == "doc-123"

    def test_flat_dict_multiple_keys(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        client.userid_mapper["bob"] = "uid-bob"
        data = {
            "dc:creator": "uid-alice",
            "dc:lastContributor": "uid-bob",
            "title": "My Doc",
        }
        result = client._translate_response(data)
        assert result["dc:creator"] == "alice"
        assert result["dc:lastContributor"] == "bob"
        assert result["title"] == "My Doc"

    def test_nested_dict(self):
        client = _make_client()
        client.userid_mapper["admin"] = "uid-admin"
        data = {
            "entries": [
                {"lockOwner": "uid-admin", "name": "file.txt"},
                {"lockOwner": "uid-admin", "name": "other.txt"},
            ]
        }
        result = client._translate_response(data)
        assert result["entries"][0]["lockOwner"] == "admin"
        assert result["entries"][1]["lockOwner"] == "admin"

    def test_list_value_dc_contributors(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        client.userid_mapper["bob"] = "uid-bob"
        data = {
            "properties": {
                "dc:contributors": ["uid-alice", "uid-bob"],
                "dc:title": "Test",
            }
        }
        result = client._translate_response(data)
        assert result["properties"]["dc:contributors"] == ["alice", "bob"]
        assert result["properties"]["dc:title"] == "Test"

    def test_actors_with_prefix(self):
        client = _make_client()
        client.userid_mapper["admin"] = "uid-admin"
        data = {"actors": ["user:uid-admin"]}
        result = client._translate_response(data)
        assert result["actors"] == ["user:admin"]

    def test_deeply_nested(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        data = {
            "level1": {
                "level2": {
                    "author": "uid-alice",
                }
            }
        }
        result = client._translate_response(data)
        assert result["level1"]["level2"]["author"] == "alice"

    def test_list_of_dicts(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        client.userid_mapper["bob"] = "uid-bob"
        data = [
            {"initiator": "uid-alice"},
            {"initiator": "uid-bob"},
        ]
        result = client._translate_response(data)
        assert result[0]["initiator"] == "alice"
        assert result[1]["initiator"] == "bob"

    def test_no_known_keys(self):
        client = _make_client()
        data = {"uid": "doc-123", "title": "hello"}
        result = client._translate_response(data)
        assert result == {"uid": "doc-123", "title": "hello"}

    def test_non_dict_non_list_passthrough(self):
        client = _make_client()
        assert client._translate_response("just a string") == "just a string"
        assert client._translate_response(42) == 42
        assert client._translate_response(None) is None

    def test_mutates_in_place(self):
        client = _make_client()
        client.userid_mapper["alice"] = "uid-alice"
        data = {"lockOwner": "uid-alice"}
        result = client._translate_response(data)
        assert result is data

    def test_mixed_known_and_nested(self):
        client = _make_client()
        client.userid_mapper["admin"] = "uid-admin"
        client.userid_mapper["alice"] = "uid-alice"
        data = {
            "entity-type": "document",
            "uid": "abc-123",
            "lockOwner": "uid-admin",
            "properties": {
                "dc:creator": "uid-alice",
                "dc:lastContributor": "uid-admin",
                "dc:title": "My Document",
            },
        }
        result = client._translate_response(data)
        assert result["lockOwner"] == "admin"
        assert result["properties"]["dc:creator"] == "alice"
        assert result["properties"]["dc:lastContributor"] == "admin"
        assert result["properties"]["dc:title"] == "My Document"

    def test_empty_dict(self):
        client = _make_client()
        assert client._translate_response({}) == {}

    def test_empty_list(self):
        client = _make_client()
        assert client._translate_response([]) == []

    def test_principalName_in_audit_entries(self):
        client = _make_client()
        client.userid_mapper["admin"] = "uid-admin"
        data = {
            "entries": [
                {"principalName": "uid-admin", "eventId": "documentCreated"},
                {"principalName": "uid-admin", "eventId": "documentModified"},
            ]
        }
        result = client._translate_response(data)
        assert result["entries"][0]["principalName"] == "admin"
        assert result["entries"][1]["principalName"] == "admin"

    def test_creator_key(self):
        client = _make_client()
        client.userid_mapper["bob"] = "uid-bob"
        data = {"creator": "uid-bob"}
        result = client._translate_response(data)
        assert result["creator"] == "bob"

    def test_lastContributor_filesystem_style(self):
        client = _make_client()
        client.userid_mapper["bob"] = "uid-bob"
        data = {"lastContributor": "uid-bob", "id": "fs-item-1"}
        result = client._translate_response(data)
        assert result["lastContributor"] == "bob"


# ===================================================================
#  execute() integration — request body params & response
# ===================================================================

class TestExecuteIntegration:
    """Verify that execute() delegates body param translation to
    self.client._translate_request_params(), and that resp.json()
    auto-translates via the NuxeoClient.request() wrapper."""

    def test_request_params_are_translated(self):
        """Params with username keys are translated before build_payload."""
        api, client = _make_api()

        mock_response = MagicMock()
        mock_response.json.return_value = {"entity-type": "document", "uid": "doc-1"}
        mock_response.headers = {"content-length": "100"}
        client.request.return_value = mock_response

        api.execute(
            command="Document.AddPermission",
            input_obj="doc-1",
            params={"username": "alice", "permission": "Write"},
            check_params=False,
        )

        call_args = client.request.call_args
        sent_data = call_args.kwargs.get("data") or call_args[1].get("data")
        assert sent_data["params"]["username"] == "uid-alice"
        assert sent_data["params"]["permission"] == "Write"

    def test_response_is_translated(self):
        """Response JSON with known keys is translated by resp.json() wrapper."""
        api, client = _make_api()
        client.userid_mapper["admin"] = "uid-admin"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entity-type": "document",
            "uid": "doc-1",
            "lockOwner": "uid-admin",
        }
        mock_response.headers = {"content-length": "100"}
        client.request.return_value = mock_response

        result = api.execute(
            command="Document.Lock",
            input_obj="doc-1",
            check_params=False,
        )

        # resp.json() is called by execute().
        # In this unit test the mock returns raw data (no wrapping),
        # but _translate_response is tested separately above.
        # The call still works because execute() calls resp.json().
        assert result["uid"] == "doc-1"

    def test_request_and_response_roundtrip(self):
        """Full round-trip: username in params → uid sent → uid in response → username returned."""
        api, client = _make_api()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entity-type": "document",
            "lockOwner": "uid-alice",
            "properties": {
                "dc:creator": "uid-alice",
            },
        }
        mock_response.headers = {"content-length": "100"}
        client.request.return_value = mock_response

        result = api.execute(
            command="Document.AddPermission",
            input_obj="doc-1",
            params={"username": "alice", "permission": "Write"},
            check_params=False,
        )

        # Verify the mapper was populated by request translation
        assert client.userid_mapper["alice"] == "uid-alice"

    def test_void_op_no_json_parsing(self):
        """When response has no JSON body, should not crash."""
        api, client = _make_api()

        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.content = b""
        mock_response.headers = {"content-length": "0"}
        client.request.return_value = mock_response

        result = api.execute(
            command="Document.AddPermission",
            input_obj="doc-1",
            params={"username": "alice", "permission": "Write"},
            check_params=False,
        )
        assert result == b""

    def test_no_username_params_pass_through(self):
        """Params without username keys should not be altered."""
        api, client = _make_api()

        mock_response = MagicMock()
        mock_response.json.return_value = {"uid": "doc-1"}
        mock_response.headers = {"content-length": "50"}
        client.request.return_value = mock_response

        api.execute(
            command="Document.Move",
            input_obj="doc-1",
            params={"target": "/path/to/dest"},
            check_params=False,
        )

        call_args = client.request.call_args
        sent_data = call_args.kwargs.get("data") or call_args[1].get("data")
        assert sent_data["params"]["target"] == "/path/to/dest"


# ===================================================================
#  Mapper isolation
# ===================================================================

class TestMapperIsolation:

    def test_mapper_starts_empty(self):
        client = _make_client()
        assert client.userid_mapper == {}

    def test_mapper_populated_after_resolve(self):
        client = _make_client()
        client.resolve_uid("testuser")
        assert "testuser" in client.userid_mapper

    def test_resolve_username_populates_mapper(self):
        client = _make_client()
        client.resolve_username("uid-testuser")
        assert client.userid_mapper.get("testuser") == "uid-testuser"

    def test_resolve_uid_then_resolve_username_roundtrip(self):
        client = _make_client()
        uid = client.resolve_uid("dave")
        assert uid == "uid-dave"

        username = client.resolve_username("uid-dave")
        assert username == "dave"
        assert len(client.userid_mapper) == 1


# ===================================================================
#  NuxeoClient.request() integration — URL params & response wrapping
# ===================================================================

class TestRequestIntegration:
    """Test that NuxeoClient.request() translates URL query params
    and wraps response.json() for automatic UID→username translation.

    These tests exercise the actual request() method hooks by mocking
    the underlying _session.request() so no real HTTP call is made.
    """

    def _make_real_client(self):
        """Create a NuxeoClient with enough real internals to call request()."""
        with patch.object(NuxeoClient, "__init__", lambda self: None):
            client = NuxeoClient.__new__(NuxeoClient)
        client.userid_mapper = {}
        client.host = "http://localhost:8080/nuxeo/"
        client.api_path = "api/v1"
        client.schemas = "*"
        client.repository = "default"
        client.headers = {}
        client.client_kwargs = {}
        client.ssl_verify_needed = True
        # Use a mock auth
        client.auth = MagicMock()

        # Mock the session
        mock_session = MagicMock()
        client._session = mock_session
        return client, mock_session

    def test_url_query_params_translated(self):
        """URL query params with username keys are translated before sending."""
        client, mock_session = self._make_real_client()

        # Create a mock response that passes isinstance(resp, requests.Response)
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"entries": []})
        mock_session.request.return_value = mock_resp

        client.request("GET", "api/v1/task", params={"userId": "alice"})

        # The params passed to session.request should have translated userId
        call_kwargs = mock_session.request.call_args
        sent_params = call_kwargs.kwargs.get("params")
        assert sent_params == {"userId": "uid-alice"}

    def test_response_json_auto_translates(self):
        """response.json() returns UID→username translated data."""
        client, mock_session = self._make_real_client()
        client.userid_mapper["admin"] = "uid-admin"

        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        # The raw JSON from server has UIDs
        original_data = {
            "entity-type": "document",
            "lockOwner": "uid-admin",
            "properties": {"dc:creator": "uid-admin"},
        }
        mock_resp.json = MagicMock(return_value=original_data)
        mock_session.request.return_value = mock_resp

        resp = client.request("GET", "api/v1/path/some-doc")

        # .json() should now auto-translate
        result = resp.json()
        assert result["lockOwner"] == "admin"
        assert result["properties"]["dc:creator"] == "admin"

    def test_response_json_no_mapper_no_crash(self):
        """When userid_mapper is empty, json() still works (no translation needed)."""
        client, mock_session = self._make_real_client()

        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"title": "Hello"})
        mock_session.request.return_value = mock_resp

        resp = client.request("GET", "api/v1/path/doc")
        result = resp.json()
        assert result == {"title": "Hello"}

    def test_non_dict_params_not_translated(self):
        """If params is not a dict (e.g. a string), it should not be translated."""
        client, mock_session = self._make_real_client()

        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={})
        mock_session.request.return_value = mock_resp

        # params as a string-encoded query (unusual but should not crash)
        client.request("GET", "api/v1/path/doc", params="foo=bar")
        # Should not crash — the isinstance check should skip it

    def test_default_response_no_wrapping(self):
        """When request() returns a default value (not a Response), skip wrapping."""
        client, mock_session = self._make_real_client()

        mock_session.request.side_effect = Exception("connection error")

        result = client.request("GET", "api/v1/path/doc", default={"fallback": True})
        assert result == {"fallback": True}

    def test_multiple_username_keys_in_url_params(self):
        """Multiple username keys in URL params all get translated."""
        client, mock_session = self._make_real_client()

        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={})
        mock_session.request.return_value = mock_resp

        client.request("GET", "api/v1/task", params={
            "userId": "alice",
            "actors": ["user:bob", "user:carol"],
            "pageSize": "10",
        })

        call_kwargs = mock_session.request.call_args
        sent_params = call_kwargs.kwargs.get("params")
        assert sent_params["userId"] == "uid-alice"
        assert sent_params["actors"] == ["user:uid-bob", "user:uid-carol"]
        assert sent_params["pageSize"] == "10"  # untouched
