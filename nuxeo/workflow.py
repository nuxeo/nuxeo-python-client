__author__ = 'loopingz'
from common import NuxeoObject


class Workflow(NuxeoObject):

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
        # Need core Nuxeo for this
        return self._service.fetch_graph(self.id)

    def fetch_tasks(self):
        return self._service.fetch_tasks({'workflowModelName': self.workflowModelName, 'workflowInstanceId': self.id})

class Task(NuxeoObject):

    def __init__(self, obj=None, service=None):
        super(Task, self).__init__(obj=obj, service=service)
        self._read(obj)


    def complete(self, action, variables=dict(), comment=None):
        # TO GET Nuxeo
        body = {'entity-type': 'task', 'id': self.get_id()}
        params = dict()
        params.update(self.variables)
        if (comment):
            params['comment'] = comment
        params.update(variables)
        body['variables']=variables
        self._read(self._service._service.request('task/' + self.get_id() + '/' + action, body=body, method="PUT"))
        return self


    def reassign(self, actors, comment=None):
        query_params = dict()
        query_params['actors'] = actors
        if comment:
            query_params['comment'] = comment
        self._read(self._service._service.request('task/' + self.get_id() + '/reassign', query_params=query_params, method="PUT"))


    def delegate(self, actors, comment=None):
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

    def __init__(self, service):
        self._service = service

    def start(self, workflowModelName, workflowOptions = dict(), url=None):
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
        print url
        return Workflow(self._service.request(url, body=body, method="POST"), service=self)

    def fetch_started_workflows(self, name):
        return self._map(self._service.request('workflow?workflowModelName=' + name, method="GET"), Workflow)

    def _map(self, result, clazz):
        tasks = []
        for task in result['entries']:
            tasks.append(clazz(task, self))
        return tasks

    def fetch_graph(self, id):
        return self._service.request('workflow/' + id + '/graph')

    def fetch_tasks(self, options=dict()):
        return self._map(self._service.request('task', method="GET", query_params=options), Task)

