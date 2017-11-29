# coding: utf-8
from __future__ import unicode_literals

from urllib2 import HTTPError

import pytest
import socket


@pytest.fixture(scope='function')
def workflows(server, clean_root):
    try:
        server.repository().delete('/task-root')
    except (HTTPError, socket.timeout):
        pass
    try:
        server.repository().delete('/document-route-instances-root')
    except (HTTPError, socket.timeout):
        pass
    return server.workflows()


def test_basic_workflow(workflows, blob_file):
    doc = blob_file
    workflow = doc.start_workflow('SerialDocumentReview')
    assert workflow is not None
    wfs = workflows.fetch_started_workflows('SerialDocumentReview')
    assert len(wfs) == 1
    tasks = workflows.fetch_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    infos = {
        'participants': ['user:Administrator'],
        'assignees': ['user:Administrator'],
        'end_date': '2011-10-23T12:00:00.00Z'}
    task.complete('start_review', infos, comment='a comment')
    workflows = doc.fetch_workflows()
    assert len(workflows) == 1
    assert task.state == 'ended'
    tasks = workflow.fetch_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    task.complete('validate', {'comment': 'a comment'})
    assert task.state == 'ended'
    workflows = doc.fetch_workflows()
    assert len(workflows) == 0


def test_get_workflows(workflows):
    workflow = workflows.start('SerialDocumentReview')
    assert workflow is not None
    wfs = workflows.fetch_started_workflows('SerialDocumentReview')
    assert len(wfs) == 1
    tasks = workflows.fetch_tasks()
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id()})
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks({'workflowInstanceId': 'unknown'})
    assert len(tasks) == 0
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id(), 'userId': 'Administrator'})
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id(),
         'userId': 'Georges Abitbol'})
    assert len(tasks) == 0
    tasks = workflows.fetch_tasks(
        {'workflowInstanceId': wfs[0].get_id(),
         'workflowModelName': 'SerialDocumentReview'})
    assert len(tasks) == 1
    tasks = workflows.fetch_tasks({'workflowModelName': 'foo'})
    assert len(tasks) == 0


def test_fetch_graph(workflows):
    workflow = workflows.start('SerialDocumentReview')
    assert workflow is not None
    wfs = workflows.fetch_started_workflows('SerialDocumentReview')
    assert len(wfs) == 1
    workflow = wfs[0]
    graph = workflow.fetch_graph()
    assert graph is not None
