# coding: utf-8
from __future__ import unicode_literals

from nuxeo.models import Comment, Document

from .constants import WORKSPACE_NAME, WORKSPACE_ROOT

document = Document(
    name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"}
)


def test_crud(server):
    doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
    try:
        # At first, the document has no comment
        assert not doc.comments()

        # Create a comment for that document
        new_comment = Comment(parentId=doc.uid, text="This is my comment")
        comment = server.comments.create(new_comment)

        # Check we can retrieve the comment with its ID
        assert server.comments.get(comment.uid)

        # There is now 1 comment
        comments = doc.comments()
        assert len(comments) == 1
        assert comments[0].text == "This is my comment"

        # Update that comment
        comment.text = "Comment modified"
        comment.save()

        # Check the text has changed
        assert doc.comments()[0].text == "Comment modified"

        # Delete the comment
        comment.delete()

        # Check there si no comments for the document
        assert not doc.comments()
    finally:
        doc.delete()


def test_document_comment(server):
    """Test the Document.comment() method, it is a simple helper."""
    doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
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


def test_get_params(server):
    """Test GET parameters that allow to retrieve partial list of comments."""
    doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
    try:
        # Create a bunch of comments for that document
        for idx in range(8):
            doc.comment("This is my comment n° {}".format(idx))

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
