# coding: utf-8
import operator
import time
from uuid import uuid4

import pytest
from nuxeo.exceptions import (
    BadQuery,
    HTTPError,
    UnavailableConvertor,
    NotRegisteredConvertor,
    UnavailableBogusConvertor,
)
from nuxeo.models import BufferBlob, Document
from nuxeo.utils import version_lt

from .constants import WORKSPACE_ROOT, SSL_VERIFY


class Doc(object):
    def __init__(self, server, with_blob=False, doc_type="File"):
        self.server = server
        self.blob = with_blob
        self.filename = f"ndt-{uuid4()}.txt"
        self.doc_type = doc_type

    def __enter__(self):
        doc = Document(
            name=self.filename,
            type=self.doc_type,
            properties={"dc:title": self.filename},
        )
        self.doc = self.server.documents.create(doc, parent_path=WORKSPACE_ROOT)

        if self.blob:
            blob = BufferBlob(
                data=self.filename, name=self.filename, mimetype="text/plain"
            )
            batch = self.server.uploads.batch()
            blob = batch.upload(blob)
            self.doc.properties["file:content"] = blob
            self.doc.save()
        return self.doc

    def __exit__(self, *args):
        while "trying to delete":
            try:
                self.doc.delete()
            except HTTPError as exc:
                if exc.status == 404:
                    break
                elif exc.status == 409:
                    # Concurrent update: I think this is related to async
                    # workers hanlding the file even if the test is finished.
                    # Let's retry.
                    continue
            else:
                break


def test_add_remove_permission(server):
    with Doc(server) as doc:
        doc.add_permission({"username": "members", "permission": "Write"})
        acls = doc.fetch_acls()
        assert len(acls) == 2
        assert acls[0]["name"] == "local"
        assert acls[0]["aces"][0]["id"] == "members:Write:true:Administrator::"
        doc.remove_permission({"id": "members:Write:true:Administrator::"})
        acls = doc.fetch_acls()
        assert len(acls) == 1
        assert acls[0]["name"] == "inherited"


def test_bogus_converter(monkeypatch, server):
    converter = "converterthatdoesnotexist"

    def get(*args, **kwargs):
        """Mimic the error message when a converter does not exists."""
        raise HTTPError(message=f"{converter} is not registered")

    with Doc(server) as doc:
        monkeypatch.setattr("nuxeo.endpoint.APIEndpoint.get", get)
        with pytest.raises(NotRegisteredConvertor) as e:
            doc.convert({"converter": converter})
        assert isinstance(e.value, NotRegisteredConvertor)
        assert str(e.value).startswith(
            "ConvertorNotRegistered: conversion with options"
        )


def test_unavailable_converter(monkeypatch, server):
    converter = "converterthatisunavailable"

    def get(*args, **kwargs):
        """Mimic the error message when a converter is not available."""
        raise HTTPError(message=f"{converter} is not available")

    with Doc(server) as doc:
        monkeypatch.setattr("nuxeo.endpoint.APIEndpoint.get", get)
        with pytest.raises(UnavailableConvertor) as e:
            doc.convert({"converter": converter})
        assert isinstance(e.value, UnavailableConvertor)
        assert str(e.value).startswith("UnavailableConvertor: conversion with options")


def test_unavailable_bogus_converter(monkeypatch, server):
    converter = "converterthatisunavailableordoesnotexists"

    def get(*args, **kwargs):
        """Mimic the error message when a converter is not available."""
        raise HTTPError(message="Internal Server Error")

    with Doc(server) as doc:
        monkeypatch.setattr("nuxeo.endpoint.APIEndpoint.get", get)
        with pytest.raises(UnavailableBogusConvertor) as e:
            doc.convert({"converter": converter})
        assert isinstance(e.value, UnavailableBogusConvertor)
        assert str(e.value).startswith("Internal Server Error or Converter ")


def test_convert(server):
    with Doc(server, with_blob=True) as doc:
        try:
            res = doc.convert({"format": "html"})
            assert b"<html" in res
            assert doc.properties["dc:title"].encode("utf-8") in res
        except UnavailableConvertor:
            pytest.mark.xfail("No more converters (NXP-28123)")


def test_convert_given_converter(server):
    with Doc(server, with_blob=True) as doc:
        try:
            res = doc.convert({"converter": "office2html"})
            assert b"<html" in res
            assert doc.properties["dc:title"].encode("utf-8") in res
        except UnavailableConvertor:
            pytest.mark.xfail("No more converters (NXP-28123)")


def test_convert_missing_args(server):
    with Doc(server) as doc:
        with pytest.raises(BadQuery):
            doc.convert({})


def test_convert_unavailable(server, monkeypatch):
    def raise_convert(api, uid, options):
        raise UnavailableConvertor(options)

    monkeypatch.setattr("nuxeo.documents.API.convert", raise_convert)

    with Doc(server, with_blob=True) as doc:
        with pytest.raises(UnavailableConvertor) as e:
            doc.convert({"converter": "office2html"})
        assert str(e.value)
        msg = e.value.message
        assert msg.startswith("UnavailableConvertor: conversion with options")
        assert msg.endswith("is not available")


def test_convert_xpath(server):
    with Doc(server, with_blob=True) as doc:
        try:
            res = doc.convert({"xpath": "file:content", "type": "text/html"})
            assert b"<html" in res
            assert doc.properties["dc:title"].encode("utf-8") in res
        except UnavailableConvertor:
            pytest.mark.xfail("No more converters (NXP-28123)")


def test_create_doc_and_delete(server):
    with Doc(server, doc_type="Workspace") as doc:
        assert isinstance(doc, Document)
        assert doc.path.startswith(WORKSPACE_ROOT)
        assert doc.type == "Workspace"
        assert doc.get("dc:title").startswith("ndt-")
        assert doc.get("dc:title").endswith(".txt")
        assert server.documents.exists(path=doc.path)
    assert not server.documents.exists(path=doc.path, ssl_verify=SSL_VERIFY)


def test_create_doc_with_space_and_delete(server):
    document = Doc(server, doc_type="Workspace")
    document.filename += " (2)"
    with document as doc:
        assert isinstance(doc, Document)
        assert " " in doc.title
        assert " " in doc.get("dc:title")
        server.documents.get(path=doc.path)


def test_fetch_acls(server):
    with Doc(server) as doc:
        acls = doc.fetch_acls()
        assert len(acls) == 1
        assert acls[0]["name"] == "inherited"

        aces = sorted(acls[0]["aces"], key=operator.itemgetter("id"))
        # 2 on Jenkins, 3 locally ...
        assert len(aces) in (2, 3)
        assert aces[0]["id"] == "Administrator:Everything:true:::"
        assert aces[1]["id"] == "members:Read:true:::"
        if len(aces) == 3:
            # Starts with username, hard to guess
            assert aces[2]["id"].endswith(":ReadWrite:true:::")


def test_fetch_audit(server):
    with Doc(server) as doc:
        time.sleep(5)

        audit = doc.fetch_audit()
        if not audit["entries"]:
            pytest.xfail("No enough time for the Audit Log.")

        assert len(audit["entries"]) == 1
        entry = audit["entries"][0]
        assert entry
        assert entry["eventId"] == "documentCreated"
        assert entry["entity-type"] == "logEntry"
        assert entry["docType"] == doc.type
        assert entry["docPath"] == doc.path


def test_fetch_blob(server):
    with Doc(server, with_blob=True) as doc:
        assert doc.fetch_blob() == doc.properties["dc:title"].encode("utf-8")


def test_fetch_non_existing(server):
    assert not server.documents.exists(path="/zone51")


def test_fetch_rendition(server):
    with Doc(server, with_blob=True) as doc:
        res = doc.fetch_rendition("xmlExport")
        assert b'<?xml version="1.0" encoding="UTF-8"?>' in res
        path = f"<path>{doc.path.lstrip('/')}</path>"
        assert path.encode("utf-8") in res


def test_fetch_renditions(server):
    with Doc(server, with_blob=True) as doc:
        res = doc.fetch_renditions()
        assert "thumbnail" in res
        assert "xmlExport" in res
        assert "zipExport" in res


def test_fetch_root(server):
    root = server.documents.get(path="/")
    assert isinstance(root, Document)


def test_has_permission(server):
    with Doc(server) as doc:
        assert doc.has_permission("Write")
        assert not doc.has_permission("Foo")


def test_locking(server):
    with Doc(server) as doc:
        assert not doc.fetch_lock_status()
        assert not doc.is_locked()

        doc.lock()
        status = doc.fetch_lock_status()
        assert status["lockOwner"] == "Administrator"
        assert "lockCreated" in status
        assert doc.is_locked()

        # Double locking with the same user should work if the server has NXP-24359
        if not version_lt(server.client.server_version, "11.1"):
            doc.lock()

        doc.unlock()
        assert not doc.is_locked()


def test_page_provider(server):
    doc = server.documents.get(path="/default-domain")
    docs = server.documents.query(
        {"pageProvider": "CURRENT_DOC_CHILDREN", "queryParams": [doc.uid]}
    )
    assert docs["numberOfPages"] == 1
    assert docs["resultsCount"] == 3
    assert docs["currentPageSize"] == 3
    assert not docs["currentPageIndex"]
    assert len(docs["entries"]) == 3


def test_page_provider_pagination(server):
    doc = server.documents.get(path="/default-domain")
    docs = server.documents.query(
        {
            "pageProvider": "document_content",
            "queryParams": [doc.uid],
            "pageSize": 1,
            "currentPageIndex": 0,
            "sortBy": "dc:title",
            "sortOrder": "asc",
        }
    )
    assert docs["currentPageSize"] == 1
    assert not docs["currentPageIndex"]
    assert docs["isNextPageAvailable"]
    assert len(docs["entries"]) == 1
    assert isinstance(docs["entries"][0], Document)
    assert docs["entries"][0].title
    docs = server.documents.query(
        {
            "pageProvider": "document_content",
            "queryParams": [doc.uid],
            "pageSize": 1,
            "currentPageIndex": 1,
            "sortBy": "dc:title",
            "sortOrder": "asc",
        }
    )
    assert docs["currentPageSize"] == 1
    assert docs["currentPageIndex"] == 1
    assert docs["isNextPageAvailable"]
    assert len(docs["entries"]) == 1
    assert isinstance(docs["entries"][0], Document)
    assert docs["entries"][0].title == "Templates"
    docs = server.documents.query(
        {
            "pageProvider": "document_content",
            "queryParams": [doc.uid],
            "pageSize": 1,
            "currentPageIndex": 2,
            "sortBy": "dc:title",
            "sortOrder": "asc",
        }
    )
    assert docs["currentPageSize"] == 1
    assert docs["currentPageIndex"] == 2
    assert not docs["isNextPageAvailable"]
    assert len(docs["entries"]) == 1
    assert isinstance(docs["entries"][0], Document)
    assert docs["entries"][0].title


def test_query(server):
    docs = server.documents.query(
        {"query": "SELECT * FROM Document WHERE ecm:primaryType = 'Domain'"}
    )
    assert docs["numberOfPages"] == 1
    assert docs["resultsCount"] > 0
    assert docs["currentPageSize"] == 1
    assert not docs["currentPageIndex"]
    assert len(docs["entries"]) == 1
    assert isinstance(docs["entries"][0], Document)


def test_query_missing_args(server):
    with pytest.raises(BadQuery):
        server.documents.query({})


def test_update_doc_and_delete(server):
    with Doc(server, doc_type="Workspace") as doc:
        uid = doc.uid
        path = doc.path
        doc.set({"dc:title": "bar"})
        doc.save()
        doc_updated = server.documents.get(path=path)
        assert isinstance(doc_updated, Document)
        assert doc_updated.uid == uid
        assert doc_updated.path == path
        assert doc_updated.get("dc:title") == "bar"


def test_update_wrong_args(server):
    with pytest.raises(BadQuery):
        server.documents.query({})
