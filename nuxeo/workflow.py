# coding: utf-8
from __future__ import unicode_literals

from typing import Any, Dict, List, Optional, Text, Type, Union

from .common import NuxeoObject

__all__ = ('Task', 'Workflow', 'Workflows')


class Task(NuxeoObject):
    """ Represent a Task from a Workflow. """

    def __init__(self, obj, service=None):
        # type: (Dict[Text, Any], Optional[Workflows]) -> None
        super(Task, self).__init__(obj=obj, service=service)
        self._read(obj)

    def complete(self, action, variables=None, comment=None):
        # type: (Text, Optional[Dict[Text, Any]], Optional[Text]) -> Task
        """
        Complete the task.

        :param action: to take
        :param variables: to add to the Task
        :param comment:
        :return: Updated task
        """

        body = {'entity-type': 'task', 'id': self.get_id()}
        params = dict()
        params.update(self.variables)
        if comment:
            params['comment'] = comment
        if variables:
            params.update(variables)
        body['variables'] = variables or {}

        # To get Nuxeo service
        req = self.service.service.request(
            'task/' + self.get_id() + '/' + action, body=body, method='PUT')
        self._read(req)
        return self

    def delegate(self, actors, comment=None):
        # type: (Text, Optional[Text]) -> None
        """ Delegate the Task to someone else. """

        query_params = {'delegatedActors': actors}
        if comment:
            query_params['comment'] = comment
        self.service.service.request(
            'task/' + self.get_id() + '/delegate',
            query_params=query_params, method='PUT')
        self.refresh()

    def reassign(self, actors, comment=None):
        # type: (Text, Optional[Text]) -> None
        """ Reassign the Task to someone else. """

        query_params = {'actors': actors}
        if comment:
            query_params['comment'] = comment
        self.service.service.request(
            'task/' + self.get_id() + '/reassign',
            query_params=query_params, method='PUT')
        self.refresh()

    def refresh(self):
        # type: () -> None
        """ Refresh the Task with latest information from the server. """
        self._read(self.service.service.request(
            'task/' + self.get_id(), method='GET'))

    def _read(self, obj):
        # type: (Dict[Text, Any]) -> None
        self.directive = obj['directive']
        self.name = obj['name']
        self.created = obj['created']
        self.variables = obj['variables']
        self.taskInfo = obj['taskInfo']
        self.state = obj['state']
        self.actors = obj['actors']
        self.dueDate = obj['dueDate']
        self.id = obj['id']
        self.targetDocumentIds = obj['targetDocumentIds']
        self.nodeName = obj['nodeName']
        self.workflowInstanceId = obj['workflowInstanceId']
        self.workflowModelName = obj['workflowModelName']


class Workflow(NuxeoObject):
    """ Represent a Workflow on the server. """

    def __init__(self, obj, service):
        # type: (Dict[Text, Any], Workflows) -> None
        super(Workflow, self).__init__(obj, service)
        self._read(obj)

    def fetch_graph(self):
        # type: () -> Dict[Text, Any]
        """
        Get the workflow graph.

        :return: Raw graph result
        """
        # Need core Nuxeo for this
        return self.service.fetch_graph(self.id)

    def fetch_tasks(self):
        # type: () -> List[Task]
        """
        :return: Tasks on this Workflow
        """
        return self.service.fetch_tasks(
            {'workflowModelName': self.workflowModelName,
             'workflowInstanceId': self.id})

    def _read(self, obj):
        # type: (Dict[Text, Any]) -> None
        self.initiator = obj['initiator']
        self.name = obj['name']
        self.title = obj['title']
        self.variables = obj['variables']
        self.workflowModelName = obj['workflowModelName']
        self.state = obj['state']
        self.graphResource = obj['graphResource']
        self.attachedDocumentIds = obj['attachedDocumentIds']
        self.id = obj['id']


class Workflows(object):
    """ Workflow services. """

    def __init__(self, service):
        # type: (Nuxeo) -> None
        self.service = service

    def fetch_graph(self, uid):
        # type: (Text) -> Dict[Text, Any]
        return self.service.request('workflow/' + uid + '/graph')

    def fetch_started_workflows(self, name):
        # type: (Text) -> List[Workflow]
        """
        Get the started workflow for a specific model.

        :param name: Model name
        :return: Workflow launched with this model
        """
        req = self.service.request('workflow?workflowModelName=' + name)
        return self.map(req, Workflow)

    def fetch_tasks(self, options=None):
        # type: (Optional[Dict[Text, Any]]) -> List[Task]
        """
        Fetch the tasks from specific workflows.

        :param options:
        :return: an Array of Task from the specified Workflows
        """
        req = self.service.request('task', query_params=options or {})
        return self.map(req, Task)

    def map(self, result, cls):
        # type: (Dict[Text, Any], Union[Type[Workflow], Type[Task]]) -> Union[List[Workflow], List[Task]]
        return [cls(item, self) for item in result['entries']]

    def start(self, model, options=None, url=None):
        # type: (Text, Optional[Dict[Text, Any]], Optional[Text]) -> Workflow
        """
        Start a workflow.

        :param model: Name of the model
        :param options: Options for the Workflow
        :param url: Use to override the default URL
        :return: The Workflow object
        """

        body = {
            'workflowModelName': model,
            'entity-type': 'workflow'
        }
        if url is None:
            url = 'workflow'
        options = options or {}
        if 'attachedDocumentIds' in options:
            body['attachedDocumentIds'] = options['attachedDocumentIds']
        if 'variables' in options:
            body['variables'] = options['variables']

        req = self.service.request(url, body=body, method='POST')
        return Workflow(req, service=self)
