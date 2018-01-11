# coding: utf-8
from __future__ import unicode_literals

import pytest

from nuxeo.exceptions import HTTPError
from nuxeo.models import Document, User


def cleanup_workflows(server):
    try:
        for wf in server.workflows.started('SerialDocumentReview'):
            server.workflows.delete(wf.uid)
    except HTTPError:
        pass


@pytest.fixture(scope='module')
def workflows(server):
    return server.workflows


@pytest.fixture(scope='module')
def tasks(server):
    return server.tasks


def test_basic_workflow(tasks, workflows, server):
    cleanup_workflows(server)
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
        assert len(workflows.of(doc)) == 1
        assert task.state == 'ended'
        tks = tasks.of(workflow)
        assert len(tks) == 1
        task = tks[0]
        # NXPY-12: Reassign task give _read() error
        task.reassign(['user:{}'.format(user.uid)], comment='a comment')
        task.complete('validate', {'comment': 'a comment'})
        assert task.state == 'ended'
        assert not workflows.of(doc)
    finally:
        user.delete()
        doc.delete()


def test_get_workflows(tasks, workflows, server):
    cleanup_workflows(server)
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


def test_fetch_graph(workflows, server):
    cleanup_workflows(server)
    assert workflows.start('SerialDocumentReview')
    wfs = workflows.started('SerialDocumentReview')
    assert len(wfs) == 1
    assert wfs[0].graph()
