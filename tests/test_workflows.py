# coding: utf-8
import socket

import pytest
from nuxeo.exceptions import BadQuery, HTTPError
from nuxeo.models import Document, Task, User

from .constants import WORKSPACE_NAME, WORKSPACE_ROOT

document = Document(
    name=WORKSPACE_NAME, type="File", properties={"dc:title": "bar.txt"}
)


@pytest.fixture(scope="function")
def workflows(server):
    try:
        for wf in server.workflows.started(None):
            wf.delete()
    except HTTPError:
        pass
    for item in ("task-root", "document-route-instances-root"):
        try:
            server.client.request("DELETE", f"repo/default/path/{item}")
        except (HTTPError, socket.timeout):
            pass
    return server.workflows


@pytest.fixture(scope="module")
def tasks(server):
    return server.tasks


def test_basic_workflow(tasks, workflows, server):
    user = User(
        properties={
            "firstName": "Georges",
            "username": "georges",
            "email": "georges@example.com",
            "password": "Test",
        }
    )
    user = server.users.create(user)
    doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
    try:
        workflow = workflows.start("SerialDocumentReview", doc)
        assert workflow
        assert repr(workflow)
        assert len(workflows.get()) == 1
        assert len(workflows.started("SerialDocumentReview")) == 1
        tks = tasks.get()
        assert len(tks) == 1
        task = tks[0]
        assert repr(task)
        infos = {
            "participants": ["user:Administrator"],
            "assignees": ["user:Administrator"],
            "end_date": "2011-10-23T12:00:00.00Z",
        }
        task.delegate([f"user:{user.uid}"], comment="a comment")
        task.complete("start_review", variables=infos, comment="another comment")
        assert len(doc.workflows) == 1
        assert task.state == "ended"
        tks = workflow.tasks
        assert len(tks) == 1
        task = tks[0]
        # NXPY-12: Reassign task give _read() error
        task.reassign([f"user:{user.uid}"], comment="other comment")
        task.complete("validate", variables={"comment": "new comment"})
        assert task.state == "ended"
        assert not doc.workflows
    finally:
        user.delete()
        doc.delete()


def test_get_workflows(tasks, workflows):
    assert workflows.start("SerialDocumentReview")
    wfs = workflows.started("SerialDocumentReview")
    assert len(wfs) == 1
    assert len(tasks.get()) == 1
    tks = tasks.get({"workflowInstanceId": wfs[0].uid})
    assert len(tks) == 1
    tks = tasks.get({"workflowInstanceId": "unknown"})
    assert not tks
    tks = tasks.get({"workflowInstanceId": wfs[0].uid, "userId": "Administrator"})
    assert len(tks) == 1
    tks = tasks.get({"workflowInstanceId": wfs[0].uid, "userId": "Georges Abitbol"})
    assert not tks
    tks = tasks.get(
        {"workflowInstanceId": wfs[0].uid, "workflowModelName": "SerialDocumentReview"}
    )
    assert len(tks) == 1
    tks = tasks.get({"workflowModelName": "foo"})
    assert not tks


def test_fetch_graph(server, workflows):
    doc = server.documents.create(document, parent_path=WORKSPACE_ROOT)
    try:
        options = {
            "attachedDocumentIds": doc.uid,
            "variables": {"initiatorComment": "This is a test comment."},
        }
        assert workflows.start("SerialDocumentReview", options=options)
        wfs = workflows.started("SerialDocumentReview")
        assert len(wfs) == 1
        assert wfs[0].graph()
    finally:
        doc.delete()


def test_task_transfer(tasks):
    task = Task()
    with pytest.raises(BadQuery) as e:
        tasks.transfer(task, "bogus_transfer", {})
    msg = str(e.value)
    assert msg == "Task transfer must be either delegate or reassign."
