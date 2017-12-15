# coding: utf-8
from __future__ import unicode_literals

import socket

import pytest
from requests import HTTPError


@pytest.fixture(scope='function')
def workflows(server):
    try:
        server.repository().delete('/task-root')
    except (HTTPError, socket.timeout):
        pass
    try:
        server.repository().delete('/document-route-instances-root')
    except (HTTPError, socket.timeout):
        pass
    return server.workflows()


def test_basic_workflow(workflows, doc, georges):
    try:
        workflow = doc.start_workflow('SerialDocumentReview')
        assert workflow
        wfs = workflows.fetch_started_workflows('SerialDocumentReview')
        assert len(wfs) == 1
        tasks = workflows.fetch_tasks()
        assert len(tasks) == 1
        task = tasks[0]
        infos = {
            'participants': ['user:Administrator'],
            'assignees': ['user:Administrator'],
            'end_date': '2011-10-23T12:00:00.00Z'}
        task.delegate(georges.id, comment='a comment')
        task.complete('start_review', infos, comment='a comment')
        assert len(doc.fetch_workflows()) == 1
        assert task.state == 'ended'
        tasks = workflow.fetch_tasks()
        assert len(tasks) == 1
        task = tasks[0]
        task.complete('validate', {'comment': 'a comment'})
        assert task.state == 'ended'
        assert not doc.fetch_workflows()
    finally:
        georges.delete()


def test_get_workflows(workflows):
    assert workflows.start('SerialDocumentReview')
    wfs = workflows.fetch_started_workflows('SerialDocumentReview')
    assert len(wfs) == 1
    assert len(workflows.fetch_tasks()) == 1
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id()})
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks({'workflowInstanceId': 'unknown'})
    assert not tasks
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id(), 'userId': 'Administrator'})
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id(),
         'userId': 'Georges Abitbol'})
    assert not tasks
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id(),
         'workflowModelName': 'SerialDocumentReview'})
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks({'workflowModelName': 'foo'})
    assert not tasks


def test_fetch_graph(workflows):
    assert workflows.start('SerialDocumentReview')
    wfs = workflows.fetch_started_workflows('SerialDocumentReview')
    assert len(wfs) == 1
    assert wfs[0].fetch_graph()
