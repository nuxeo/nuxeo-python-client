# coding: utf-8
import pytest
from nuxeo.models import Comment, Document
from nuxeo.utils import version_lt

from .constants import WORKSPACE_NAME, WORKSPACE_ROOT, SSL_VERIFY

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
        if SSL_VERIFY is False:
            comment = server.comments.create(
                doc.uid, "This is my comment", ssl_verify=False
            )
        else:
            comment = server.comments.create(doc.uid, "This is my comment")
        assert isinstance(comment, Comment)

        # Check we can retrieve the comment with its ID
        assert server.comments.get(doc.uid, uid=comment.uid)

        # There is now 1 comment
        comments = doc.comments()
        assert len(comments) == 1
        assert isinstance(comments[0], Comment)
        assert comments[0].text == "This is my comment"

        # Update that comment
        comment.text = "Comment modified"
        comment.save()

        # Check the text has changed
        comments = doc.comments()
        assert isinstance(comments[0], Comment)
        assert comments[0].text == "Comment modified"
        assert comments[0].modificationDate is not None

        # Delete the comment
        if SSL_VERIFY is False:
            comment.delete(ssl_verify=False)
        else:
            comment.delete()

        # Check there si no comments for the document
        if SSL_VERIFY is False:
            assert not doc.comments(ssl_verify=False)
        else:
            assert not doc.comments()
    finally:
        if SSL_VERIFY is False:
            doc.delete(ssl_verify=False)
        else:
            doc.delete()


def test_reply(server):
    if version_lt(server.client.server_version, "10.3"):
        pytest.skip("Nuxeo 10.3 minimum")
    if SSL_VERIFY is False:
        doc = server.documents.create(
            document, parent_path=WORKSPACE_ROOT, ssl_verify=False
        )
    else:
        doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
    try:
        # Create a comment for that document
        if SSL_VERIFY is False:
            comment = server.comments.create(
                doc.uid, "This is my comment", ssl_verify=False
            )
        else:
            comment = server.comments.create(doc.uid, "This is my comment")
        assert not comment.has_replies()

        # Add a 1st reply to that comment
        reply1 = comment.reply("This is my reply comment")
        assert isinstance(reply1, Comment)
        assert comment.has_replies()

        # Check the comment has 1 reply (refetch it to ensure data is correct)
        if SSL_VERIFY is False:
            replies = server.comments.get(doc.uid, uid=comment.uid, ssl_verify=False)
        else:
            replies = server.comments.get(doc.uid, uid=comment.uid)
        assert isinstance(replies, Comment)
        assert replies.numberOfReplies == 1
        assert replies.numberOfReplies == comment.numberOfReplies
        assert replies.lastReplyDate == reply1.creationDate

        # Add a 2nd reply to that comment
        reply2 = comment.reply("This is another reply, yeah! ᕦ(ò_óˇ)ᕤ")
        assert isinstance(reply2, Comment)
        assert comment.numberOfReplies == 2
        assert not reply2.has_replies()

        # And a reply to that 2nd reply
        last_reply = reply2.reply(
            "And a reply of the 2nd reply with \N{SNOWMAN}, boom!"
        )
        assert isinstance(last_reply, Comment)
        assert reply2.has_replies()

        # Check the comment has 2 direct replies
        if SSL_VERIFY is False:
            replies = server.comments.get(doc.uid, uid=comment.uid, ssl_verify=False)
        else:
            replies = server.comments.get(doc.uid, uid=comment.uid)
        assert replies.numberOfReplies == 2
        assert replies.lastReplyDate == reply2.creationDate

        # Check the 2nd reply has 1 reply
        if SSL_VERIFY is False:
            replies = server.comments.get(doc.uid, uid=reply2.uid, ssl_verify=False)
        else:
            replies = server.comments.get(doc.uid, uid=reply2.uid)
        assert replies.numberOfReplies == 1
        assert replies.lastReplyDate == last_reply.creationDate

        # Test partial list
        assert len(comment.replies()) == 2
        assert len(comment.replies(pageSize=1, currentPageIndex=0)) == 1
        assert len(comment.replies(pageSize=1, currentPageIndex=1)) == 1
        assert len(comment.replies(pageSize=1, currentPageIndex=2)) == 0
    finally:
        if SSL_VERIFY is False:
            doc.delete(ssl_verify=False)
        else:
            doc.delete()
