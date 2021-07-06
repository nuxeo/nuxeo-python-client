# coding: utf-8
from unittest.mock import patch

import nuxeo.constants
import pytest
from nuxeo.models import BufferBlob, Document
from nuxeo.utils import version_lt

from .constants import WORKSPACE_NAME, WORKSPACE_ROOT, WORKSPACE_TEST


class Doc(object):
    def __init__(self, server, blobs=0):
        self.server = server
        self.blobs = blobs

    def __enter__(self):
        doc = Document(
            name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"}
        )
        self.doc = self.server.documents.create(doc, parent_path=WORKSPACE_ROOT)

        if self.blobs:
            # Upload several blobs for one document
            batch = self.server.uploads.batch()
            for idx in range(self.blobs):
                blob = BufferBlob(data=f"foo {idx}", name=f"foo-{idx}.txt")
                batch.upload(blob)

            path = WORKSPACE_TEST
            batch.attach(path)
        return self.doc

    def __exit__(self, *args):
        self.doc.delete()


def test_document_create(server):
    doc = Document(
        type="File",
        name="日本.txt",
        properties={"dc:title": "日本.txt", "dc:description": "ру́сский"},
    )
    doc = server.documents.create(doc, parent_path="/")
    try:
        assert doc.entity_type == "document"
        assert doc.type == "File"
        assert doc.title == "日本.txt"
        assert doc.get("dc:title") == doc.properties["dc:title"] == "日本.txt"
        assert doc.properties["dc:description"] == "ру́сский"
    finally:
        doc.delete()
    assert not server.documents.exists(doc.uid)


def test_document_create_bytes_warning(server):
    """Running "python3 -bb -m pytest -W error test..." will fail:
    BytesWarning: str() on a bytes instance
    """
    name = "File.txt"
    properties = {"dc:title": name, "note:note": b"some content"}
    document = None
    try:
        document = server.operations.execute(
            command="Document.Create",
            input_obj="doc:" + WORKSPACE_ROOT,
            type="Note",
            name=name,
            properties=properties,
        )
    finally:
        if document:
            server.documents.delete(document["uid"])


def test_document_get_blobs(server):
    """Fetch all blobs of a given document."""

    number = 4
    with Doc(server, blobs=number) as doc:
        for idx in range(number):
            xpath = f"files:files/{idx}/file"
            blob = doc.fetch_blob(xpath)
            assert blob == f"foo {idx}".encode("utf-8")


def test_document_list_update(server):
    new_doc1 = Document(
        name="ws-js-tests1", type="Workspace", properties={"dc:title": "ws-js-tests1"}
    )
    new_doc2 = Document(
        name="ws-js-tests2", type="Workspace", properties={"dc:title": "ws-js-tests2"}
    )

    doc1 = server.documents.create(new_doc1, parent_path=WORKSPACE_ROOT)
    doc2 = server.documents.create(new_doc2, parent_path=WORKSPACE_ROOT)
    desc = "sample description"
    res = server.operations.execute(
        command="Document.Update",
        params={"properties": {"dc:description": desc}},
        input_obj=[doc1.path, doc2.path],
    )

    assert res["entity-type"] == "documents"
    assert len(res["entries"]) == 2
    assert res["entries"][0]["path"] == doc1.path
    assert res["entries"][0]["properties"]["dc:description"] == desc
    assert res["entries"][1]["path"] == doc2.path
    assert res["entries"][1]["properties"]["dc:description"] == desc
    doc1.delete()
    doc2.delete()


def test_document_move(server):
    doc = Document(name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"})
    assert repr(doc)
    folder = Document(name="Test", type="Folder", properties={"dc:title": "Test"})
    doc = server.documents.create(doc, parent_path=WORKSPACE_ROOT)
    folder = server.documents.create(folder, parent_path=WORKSPACE_ROOT)
    try:
        doc.move(WORKSPACE_ROOT + "/Test", "new name")
        assert doc.path == WORKSPACE_ROOT + "/Test/new name"
        children = server.documents.get_children(folder.uid)
        assert len(children) == 1
        assert children[0].uid == doc.uid
    finally:
        doc.delete()
        folder.delete()
    assert not server.documents.exists(path=doc.path)


def test_document_get_children_with_permissions(server):
    doc = Document(name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"})
    doc = server.documents.create(doc, parent_path=WORKSPACE_ROOT)
    try:
        # Without enrichers
        children = server.documents.get_children(path="/")
        assert len(children) == 1
        with pytest.raises(KeyError):
            assert "ReadWrite" in children[0].contextParameters["permissions"]

        # With enrichers
        children = server.documents.get_children(path="/", enrichers=["permissions"])
        assert len(children) == 1
        assert "ReadWrite" in children[0].contextParameters["permissions"]
    finally:
        doc.delete()
    assert not server.documents.exists(path=doc.path)


def test_document_get_children_with_with_provider(server):
    root = server.documents.get(path=WORKSPACE_ROOT)
    doc = Document(
        name=WORKSPACE_NAME, type="Folder", properties={"dc:title": "folder"}
    )
    doc = server.documents.create(doc, parent_path=root.path)
    try:
        enrichers = ["permissions", "hasFolderishChild"]
        opts = {
            "pageProvider": "tree_children",
            "pageSize": 1,
            "queryParams": root.uid,
        }
        children = server.documents.query(opts=opts, enrichers=enrichers)
        assert len(children["entries"]) == 1
        entry = children["entries"][0]
        assert entry.contextParameters["permissions"]
        assert "hasFolderishChild" in entry.contextParameters
    finally:
        doc.delete()


def test_document_trash(server):
    doc = Document(name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"})
    doc = server.documents.create(doc, parent_path=WORKSPACE_ROOT)
    try:
        assert not doc.isTrashed
        doc.trash()
        assert doc.isTrashed
        doc.untrash()
        assert not doc.isTrashed
    finally:
        doc.delete()


def test_follow_transition(server):
    doc = Document(name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"})
    doc = server.documents.create(doc, parent_path=WORKSPACE_ROOT)
    try:
        assert doc.state == "project"
        doc.follow_transition("approve")
        assert doc.state == "approved"
        doc.follow_transition("backToProject")
        assert doc.state == "project"
    finally:
        doc.delete()


def test_add_permission(server):
    if version_lt(server.client.server_version, "10.10"):
        pytest.skip("Nuxeo 10.10 minimum")

    with patch.object(nuxeo.constants, "CHECK_PARAMS", new=True), Doc(server) as doc:
        # NXPY-84: here we should not fail with KeyError: 'list' in check_params()
        doc.add_permission({"permission": "ReadWrite", "users": ["Administrator"]})


def test_document_comment(server):
    """Test the Document.comment() method, it is a simple helper."""
    if version_lt(server.client.server_version, "10.3"):
        pytest.skip("Nuxeo 10.3 minimum")

    doc = Document(name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"})
    doc = server.documents.create(doc, parent_path=WORKSPACE_ROOT)
    try:
        # At first, the document has no comment
        assert not doc.comments()

        # Create a comment for that document
        doc.comment("This is my super comment")

        # There is now 1 comment
        comments = doc.comments()
        assert len(comments) == 1
        assert comments[0].text == "This is my super comment"

        # Delete the comment
        server.comments.delete(comments[0].uid)
    finally:
        doc.delete()


def test_comments_with_params(server):
    """Test GET parameters that allow to retrieve partial list of comments."""
    if version_lt(server.client.server_version, "10.3"):
        pytest.skip("Nuxeo 10.3 minimum")

    doc = Document(name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"})
    doc = server.documents.create(doc, parent_path=WORKSPACE_ROOT)
    try:
        # Create a bunch of comments for that document
        for idx in range(8):
            doc.comment(f"This is my comment n° {idx}")

        # Get maximum comments with default values
        comments = doc.comments()
        assert len(comments) == 8

        # Page 1
        comments = doc.comments(pageSize=5, currentPageIndex=0)
        assert len(comments) == 5

        # Page 2
        comments = doc.comments(pageSize=5, currentPageIndex=1)
        assert len(comments) == 3

        # Page 3
        comments = doc.comments(pageSize=5, currentPageIndex=2)
        assert len(comments) == 0
    finally:
        doc.delete()
