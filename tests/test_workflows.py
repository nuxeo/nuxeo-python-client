# coding: utf-8
from __future__ import unicode_literals

import socket

import pytest

from nuxeo.exceptions import HTTPError
from nuxeo.models import Document, User


@pytest.fixture(scope='function')
def workflows(server):
    try:
        for wf in server.workflows.started(None):
            wf.delete()
    except HTTPError:
        pass
    for item in ('task-root', 'document-route-instances-root'):
        try:
            server.client.request(
                'DELETE', 'repo/default/path/{}'.format(item))
        except (HTTPError, socket.timeout):
            pass
    return server.workflows


@pytest.fixture(scope='module')
def tasks(server):
    return server.tasks


def test_basic_workflow(tasks, workflows, server):
    user = User(
        properties={
            'firstName': 'Georges',
            'username': 'georges',
            'email': 'georges@example.com',
            'password': 'Test'
        })
    user = server.users.create(user)
    doc = Document(
        name=pytest.ws_python_test_name,
        type='File',
        properties={
            'dc:title': 'bar.txt',
        }
    )
    doc = server.documents.create(
        doc, parent_path=pytest.ws_root_path)
    try:
        workflow = workflows.start('SerialDocumentReview', doc)
        assert workflow
        assert repr(workflow)
        wfs = workflows.started('SerialDocumentReview')
        assert len(wfs) == 1
        tks = tasks.get()
        assert len(tks) == 1
        task = tks[0]
        assert repr(task)
        infos = {
            'participants': ['user:Administrator'],
            'assignees': ['user:Administrator'],
            'end_date': '2011-10-23T12:00:00.00Z'}
        task.delegate(['user:{}'.format(user.uid)], comment='a comment')
        task.complete('start_review', infos, comment='a comment')
        assert len(doc.workflows) == 1
        assert task.state == 'ended'
        tks = workflow.tasks
        assert len(tks) == 1
        task = tks[0]
        # NXPY-12: Reassign task give _read() error
        task.reassign(['user:{}'.format(user.uid)], comment='a comment')
        task.complete('validate', {'comment': 'a comment'})
        assert task.state == 'ended'
        assert not doc.workflows
    finally:
        user.delete()
        doc.delete()


def test_get_workflows(tasks, workflows):
    assert workflows.start('SerialDocumentReview')
    wfs = workflows.started('SerialDocumentReview')
    assert len(wfs) == 1
    assert len(tasks.get()) == 1
    tks = tasks.get({'workflowInstanceId': wfs[0].uid})
    assert len(tks) == 1
    tks = tasks.get({'workflowInstanceId': 'unknown'})
    assert not tks
    tks = tasks.get(
        {'workflowInstanceId': wfs[0].uid, 'userId': 'Administrator'})
    assert len(tks) == 1
    tks = tasks.get({
        'workflowInstanceId': wfs[0].uid,
        'userId': 'Georges Abitbol'
    })
    assert not tks
    tks = tasks.get({
        'workflowInstanceId': wfs[0].uid,
        'workflowModelName': 'SerialDocumentReview'
    })
    assert len(tks) == 1
    tks = tasks.get({'workflowModelName': 'foo'})
    assert not tks


def test_fetch_graph(workflows):
    assert workflows.start('SerialDocumentReview')
    wfs = workflows.started('SerialDocumentReview')
    assert len(wfs) == 1
    assert wfs[0].graph()
