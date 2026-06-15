# coding: utf-8
"""
Unit tests for the userid_mapper translation layer in nuxeo.client.NuxeoClient.

Covers:
  - _translate_user_entity   (single user, entries list, nested, non-user)
  - userid_mapper population (seeding from user entity responses)
  - request() integration    (response JSON wrapping via _translate_user_entity)
  - execute() integration    (end-to-end through request wrapper)
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
    return client


def _make_api():
    """Create an operations API instance with a mocked client."""
    client = _make_client()
    # Set minimal attributes needed by APIEndpoint / API
    client.api_path = "api/v1"
    # Mock request to avoid real HTTP calls
    client.request = MagicMock()
    api = API(client)
    return api, client


# ===================================================================
#  _translate_user_entity - single user entities
# ===================================================================


class TestTranslateUserEntitySingle:
    """Verify single user entity translation and mapper seeding."""

    def test_user_entity_id_replaced_with_username(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "abc-123-uuid",
            "properties": {"username": "alice"},
        }
        result = client._translate_user_entity(data)
        assert result["id"] == "alice"

    def test_mapper_seeded_on_mismatch(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "abc-123-uuid",
            "properties": {"username": "alice"},
        }
        client._translate_user_entity(data)
        assert client.userid_mapper == {"alice": "abc-123-uuid"}

    def test_no_translation_when_id_equals_username(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "alice",
            "properties": {"username": "alice"},
        }
        result = client._translate_user_entity(data)
        assert result["id"] == "alice"
        assert client.userid_mapper == {}

    def test_no_translation_without_username_property(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "abc-123-uuid",
            "properties": {},
        }
        result = client._translate_user_entity(data)
        assert result["id"] == "abc-123-uuid"
        assert client.userid_mapper == {}

    def test_no_translation_without_properties(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "abc-123-uuid",
        }
        result = client._translate_user_entity(data)
        assert result["id"] == "abc-123-uuid"
        assert client.userid_mapper == {}

    def test_no_translation_without_id(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "properties": {"username": "alice"},
        }
        client._translate_user_entity(data)
        assert client.userid_mapper == {}
        """_translate_user_entity returns the (possibly mutated) data."""
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "uid-abc",
            "properties": {"username": "bob"},
        }
        result = client._translate_user_entity(data)
        assert result is data

    def test_mutates_in_place(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "uid-abc",
            "properties": {"username": "bob"},
        }
        client._translate_user_entity(data)
        assert data["id"] == "bob"


# ===================================================================
#  _translate_user_entity - entries / list handling
# ===================================================================


class TestTranslateUserEntityEntries:
    """Verify translation handles entries lists and plain lists."""

    def test_entries_list(self):
        client = _make_client()
        data = {
            "entity-type": "users",
            "entries": [
                {
                    "entity-type": "user",
                    "id": "uid-1",
                    "properties": {"username": "alice"},
                },
                {
                    "entity-type": "user",
                    "id": "uid-2",
                    "properties": {"username": "bob"},
                },
            ],
        }
        result = client._translate_user_entity(data)
        assert result["entries"][0]["id"] == "alice"
        assert result["entries"][1]["id"] == "bob"
        assert client.userid_mapper == {"alice": "uid-1", "bob": "uid-2"}

    def test_plain_list_of_user_entities(self):
        client = _make_client()
        data = [
            {
                "entity-type": "user",
                "id": "uid-1",
                "properties": {"username": "alice"},
            },
            {
                "entity-type": "user",
                "id": "uid-2",
                "properties": {"username": "bob"},
            },
        ]
        result = client._translate_user_entity(data)
        assert result[0]["id"] == "alice"
        assert result[1]["id"] == "bob"
        assert client.userid_mapper == {"alice": "uid-1", "bob": "uid-2"}

    def test_entries_with_mixed_entity_types(self):
        client = _make_client()
        data = {
            "entries": [
                {
                    "entity-type": "user",
                    "id": "uid-1",
                    "properties": {"username": "alice"},
                },
                {
                    "entity-type": "document",
                    "id": "doc-123",
                    "properties": {"dc:title": "My Doc"},
                },
            ],
        }
        result = client._translate_user_entity(data)
        assert result["entries"][0]["id"] == "alice"
        assert result["entries"][1]["id"] == "doc-123"
        assert client.userid_mapper == {"alice": "uid-1"}

    def test_entries_already_matching(self):
        """Entries where id == username should not be touched."""
        client = _make_client()
        data = {
            "entries": [
                {
                    "entity-type": "user",
                    "id": "alice",
                    "properties": {"username": "alice"},
                },
            ],
        }
        result = client._translate_user_entity(data)
        assert result["entries"][0]["id"] == "alice"
        assert client.userid_mapper == {}

    def test_empty_entries(self):
        client = _make_client()
        data = {"entity-type": "users", "entries": []}
        result = client._translate_user_entity(data)
        assert result["entries"] == []
        assert client.userid_mapper == {}


# ===================================================================
#  _translate_user_entity - non-user / edge cases
# ===================================================================


class TestTranslateUserEntityEdgeCases:
    def test_non_user_entity_not_translated(self):
        client = _make_client()
        data = {
            "entity-type": "document",
            "id": "doc-uuid",
            "properties": {"dc:title": "My Doc"},
        }
        result = client._translate_user_entity(data)
        assert result["id"] == "doc-uuid"
        assert client.userid_mapper == {}

    def test_non_dict_non_list_passthrough(self):
        client = _make_client()
        assert client._translate_user_entity("just a string") == "just a string"
        assert client._translate_user_entity(42) == 42
        assert client._translate_user_entity(None) is None

    def test_empty_dict(self):
        client = _make_client()
        assert client._translate_user_entity({}) == {}

    def test_empty_list(self):
        client = _make_client()
        assert client._translate_user_entity([]) == []

    def test_dict_without_entity_type(self):
        client = _make_client()
        data = {"id": "something", "properties": {"username": "alice"}}
        result = client._translate_user_entity(data)
        assert result["id"] == "something"
        assert client.userid_mapper == {}

    def test_properties_is_none(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "uid-abc",
            "properties": None,
        }
        result = client._translate_user_entity(data)
        assert result["id"] == "uid-abc"
        assert client.userid_mapper == {}

    def test_multiple_users_populate_mapper(self):
        client = _make_client()
        data1 = {
            "entity-type": "user",
            "id": "uid-1",
            "properties": {"username": "alice"},
        }
        data2 = {
            "entity-type": "user",
            "id": "uid-2",
            "properties": {"username": "bob"},
        }
        client._translate_user_entity(data1)
        client._translate_user_entity(data2)
        assert len(client.userid_mapper) == 2
        assert client.userid_mapper["alice"] == "uid-1"
        assert client.userid_mapper["bob"] == "uid-2"


# ===================================================================
#  Mapper isolation
# ===================================================================


class TestMapperIsolation:
    def test_mapper_starts_empty(self):
        client = _make_client()
        assert client.userid_mapper == {}

    def test_mapper_populated_after_translate(self):
        client = _make_client()
        data = {
            "entity-type": "user",
            "id": "uid-test",
            "properties": {"username": "testuser"},
        }
        client._translate_user_entity(data)
        assert "testuser" in client.userid_mapper

    def test_separate_clients_have_separate_mappers(self):
        client1 = _make_client()
        client2 = _make_client()
        data = {
            "entity-type": "user",
            "id": "uid-1",
            "properties": {"username": "alice"},
        }
        client1._translate_user_entity(data)
        assert "alice" in client1.userid_mapper
        assert "alice" not in client2.userid_mapper


# ===================================================================
#  NuxeoClient.request() integration - response wrapping
# ===================================================================


class TestRequestIntegration:
    """Test that NuxeoClient.request() wraps response.json() to call
    _translate_user_entity automatically."""

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
        client.auth = MagicMock()
        mock_session = MagicMock()
        client._session = mock_session
        return client, mock_session

    def test_response_json_translates_user_entity(self):
        """response.json() should auto-translate user entity responses."""
        client, mock_session = self._make_real_client()

        original_data = {
            "entity-type": "user",
            "id": "uid-admin",
            "properties": {"username": "admin"},
        }
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=original_data)
        mock_session.request.return_value = mock_resp

        resp = client.request("GET", "api/v1/user/admin")
        result = resp.json()
        assert result["id"] == "admin"
        assert client.userid_mapper == {"admin": "uid-admin"}

    def test_response_json_no_user_entity_no_crash(self):
        """When response has no user entities, json() still works."""
        client, mock_session = self._make_real_client()

        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"title": "Hello"})
        mock_session.request.return_value = mock_resp

        resp = client.request("GET", "api/v1/path/doc")
        result = resp.json()
        assert result == {"title": "Hello"}

    def test_response_json_translates_entries(self):
        """response.json() translates user entities embedded in entries."""
        client, mock_session = self._make_real_client()

        original_data = {
            "entity-type": "users",
            "entries": [
                {
                    "entity-type": "user",
                    "id": "uid-1",
                    "properties": {"username": "alice"},
                },
                {
                    "entity-type": "user",
                    "id": "uid-2",
                    "properties": {"username": "bob"},
                },
            ],
        }
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value=original_data)
        mock_session.request.return_value = mock_resp

        resp = client.request("GET", "api/v1/user")
        result = resp.json()
        assert result["entries"][0]["id"] == "alice"
        assert result["entries"][1]["id"] == "bob"
        assert client.userid_mapper == {"alice": "uid-1", "bob": "uid-2"}

    def test_default_response_no_wrapping(self):
        """When request() returns a default value (not a Response), skip wrapping."""
        client, mock_session = self._make_real_client()

        mock_session.request.side_effect = Exception("connection error")

        result = client.request("GET", "api/v1/path/doc", default={"fallback": True})
        assert result == {"fallback": True}


# ===================================================================
#  execute() integration - end-to-end through request wrapper
# ===================================================================


class TestExecuteIntegration:
    """Verify that execute() works correctly with the response JSON
    wrapping via NuxeoClient.request()."""

    def test_execute_returns_json(self):
        """execute() returns the JSON response."""
        api, client = _make_api()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entity-type": "document",
            "uid": "doc-1",
        }
        mock_response.headers = {"content-length": "100"}
        client.request.return_value = mock_response

        result = api.execute(
            command="Document.Fetch",
            input_obj="doc-1",
            check_params=False,
        )
        assert result["uid"] == "doc-1"

    def test_params_passed_through(self):
        """Params are passed through to the request payload."""
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

    def test_void_op_no_json_parsing(self):
        """When response has no JSON body, should not crash."""
        api, client = _make_api()

        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.content = b""
        mock_response.headers = {"content-length": "0"}
        client.request.return_value = mock_response

        result = api.execute(
            command="Document.Delete",
            input_obj="doc-1",
            check_params=False,
        )
        assert result == b""
