# coding: utf-8
from .common import NuxeoObject


class Workflow(NuxeoObject):
    """
    Represent a Workflow on the server
    """

    def __init__(self, obj=None, service=None):
        super(Workflow, self).__init__(obj=obj, service=service)
        self._read(obj)

    def _read(self, obj):
        self.initiator = obj['initiator']
        self.name = obj['name']
        self.title = obj['title']
        self.variables = obj['variables']
        self.workflowModelName = obj['workflowModelName']
        self.state = obj['state']
        self.graphResource = obj['graphResource']
        self.attachedDocumentIds = obj['attachedDocumentIds']
        self.id = obj['id']

    def fetch_graph(self):
        """
        Get the workflow graph

        :return: Raw graph result
        """
        # Need core Nuxeo for this
        return self._service.fetch_graph(self.id)

    def fetch_tasks(self):
        """

        :return: Tasks on this Workflow
        """
        return self._service.fetch_tasks({'workflowModelName': self.workflowModelName, 'workflowInstanceId': self.id})


class Task(NuxeoObject):
    """
    Represent a Task from a Workflow
    """

    def __init__(self, obj=None, service=None):
        super(Task, self).__init__(obj=obj, service=service)
        self._read(obj)

    def complete(self, action, variables=dict(), comment=None):
        """
        Complete the task

        :param action: to take
        :param variables: to add to the Task
        :param comment:
        :return: Updated task
        """
        body = {'entity-type': 'task', 'id': self.get_id()}
        params = dict()
        params.update(self.variables)
        if (comment):
            params['comment'] = comment
        params.update(variables)
        body['variables']=variables
        # To get Nuxeo service
        self._read(self._service._service.request('task/' + self.get_id() + '/' + action, body=body, method="PUT"))
        return self

    def reassign(self, actors, comment=None):
        """
        Reassign the Task to someone else

        :param actors:
        :param comment:
        """
        query_params = dict()
        query_params['actors'] = actors
        if comment:
            query_params['comment'] = comment
        self._read(self._service._service.request('task/' + self.get_id() + '/reassign', query_params=query_params, method="PUT"))

    def delegate(self, actors, comment=None):
        """
        Delegate the Task to someone else

        :param actors:
        :param comment:
        """
        query_params = dict()
        query_params['delegatedActors'] = actors
        if comment:
            query_params['comment'] = comment
        self._read(self._service._service.request('task/' + self.get_id() + '/delegate', query_params=query_params, method="PUT"))

    def _read(self, obj):
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


class Workflows():
    """
    Workflow services
    """
    def __init__(self, service):
        self._service = service

    def start(self, workflowModelName, workflowOptions = dict(), url=None):
        """
        Start a workflow

        :param workflowModelName: Name of the model
        :param workflowOptions: Options for the Workflow
        :param url: Use to override the default URL
        :return: The Workflow object
        """
        body = {
            'workflowModelName': workflowModelName,
            'entity-type': 'workflow'
        }
        if url is None:
            url = 'workflow'
        if "attachedDocumentIds" in workflowOptions:
            body['attachedDocumentIds'] = workflowOptions["attachedDocumentIds"]
        if "variables" in workflowOptions:
            body['variables'] = workflowOptions["variables"]
        return Workflow(self._service.request(url, body=body, method="POST"), service=self)

    def fetch_started_workflows(self, name):
        """
        Get the started workflow for a specific model

        :param name: Model name
        :return: Workflow launched with this model
        """
        return self._map(self._service.request('workflow?workflowModelName=' + name, method="GET"), Workflow)

    def _map(self, result, clazz):
        tasks = []
        for task in result['entries']:
            tasks.append(clazz(task, self))
        return tasks

    def fetch_graph(self, id):
        return self._service.request('workflow/' + id + '/graph')

    def fetch_tasks(self, options=dict()):
        """
        Fetch the tasks from specific workflows

        :param options:
        :return: an Array of Task from the specified Workflows
        """
        return self._map(self._service.request('task', method="GET", query_params=options), Task)

