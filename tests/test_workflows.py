# coding: utf-8
from __future__ import unicode_literals

import pytest


@pytest.fixture(scope='function')
def workflows(server):
    for wf in server.workflows.started('SerialDocumentReview'):
        server.workflows.delete(wf.id)
    return server.workflows


@pytest.fixture(scope='module')
def tasks(server):
    return server.tasks


def test_basic_workflow(tasks, workflows, doc, georges):
    try:
        workflow = workflows.start('SerialDocumentReview', doc)
        assert workflow
        wfs = workflows.started('SerialDocumentReview')
        assert len(wfs) == 1
        tks = tasks.get()
        assert len(tks) == 1
        task = tks[0]
        infos = {
            'participants': ['user:Administrator'],
            'assignees': ['user:Administrator'],
            'end_date': '2011-10-23T12:00:00.00Z'}
        task.delegate(['user:{}'.format(georges.id)], comment='a comment')
        task.complete('start_review', infos, comment='a comment')
        assert len(workflows.of(doc)) == 1
        assert task.state == 'ended'
        tks = tasks.of(workflow)
        assert len(tks) == 1
        task = tks[0]
        # NXPY-12: Reassign task give _read() error
        task.reassign(['user:{}'.format(georges.id)], comment='a comment')
        task.complete('validate', {'comment': 'a comment'})
        assert task.state == 'ended'
        assert not workflows.of(doc)
    finally:
        georges.delete()


def test_get_workflows(tasks, workflows):
    assert workflows.start('SerialDocumentReview')
    wfs = workflows.started('SerialDocumentReview')
    assert len(wfs) == 1
    assert len(tasks.get()) == 1
    tks = tasks.get({'workflowInstanceId': wfs[0].id})
    assert len(tks) == 1
    tks = tasks.get({'workflowInstanceId': 'unknown'})
    assert not tks
    tks = tasks.get(
        {'workflowInstanceId': wfs[0].id, 'userId': 'Administrator'})
    assert len(tks) == 1
    tks = tasks.get({
        'workflowInstanceId': wfs[0].id,
        'userId': 'Georges Abitbol'
    })
    assert not tks
    tks = tasks.get({
        'workflowInstanceId': wfs[0].id,
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
