# coding: utf-8
from __future__ import unicode_literals

import pytest
from nuxeo.models import Comment, Document

from .constants import WORKSPACE_NAME, WORKSPACE_ROOT
from . import version_lt

document = Document(
    name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"}
)


def test_crud(server):
    if version_lt(server.client.server_version, "10.3"):
        pytest.skip("Nuxeo 10.3 minimum")

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
        assert doc.comments()[0].modificationDate is not None

        # Delete the comment
        comment.delete()

        # Check there si no comments for the document
        assert not doc.comments()
    finally:
        doc.delete()


def test_reply(server):
    if version_lt(server.client.server_version, "10.3"):
        pytest.skip("Nuxeo 10.3 minimum")

    doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
    try:
        # Create a comment for that document
        new_comment = Comment(parentId=doc.uid, text="This is my comment")
        comment = server.comments.create(new_comment)
        assert not comment.has_replies()

        # Add a 1st reply to that comment
        reply1 = comment.reply("This is my reply comment")
        assert comment.has_replies()

        # Check the comment has 1 reply (refetch it to ensure data is correct)
        replies = server.comments.get(comment.uid)
        assert replies.numberOfReplies == 1
        assert replies.numberOfReplies == comment.numberOfReplies
        assert replies.lastReplyDate == reply1.creationDate

        # Add a 2nd reply to that comment
        reply2 = comment.reply("This is another reply, yeah! ᕦ(ò_óˇ)ᕤ")
        assert comment.numberOfReplies == 2
        assert not reply2.has_replies()

        # And a reply to that 2nd reply
        last_reply = reply2.reply(
            "And a reply of the 2nd reply with \N{SNOWMAN}, boom!"
        )
        assert reply2.has_replies()

        # Check the comment has 2 direct replies
        replies = server.comments.get(comment.uid)
        assert replies.numberOfReplies == 2
        assert replies.lastReplyDate == reply2.creationDate

        # Check the 2nd reply has 1 reply
        replies = server.comments.get(reply2.uid)
        assert replies.numberOfReplies == 1
        assert replies.lastReplyDate == last_reply.creationDate

        # Test partial list
        assert len(comment.replies()) == 2
        assert len(comment.replies(pageSize=1, currentPageIndex=0)) == 1
        assert len(comment.replies(pageSize=1, currentPageIndex=1)) == 1
        assert len(comment.replies(pageSize=1, currentPageIndex=2)) == 0
    finally:
        doc.delete()
