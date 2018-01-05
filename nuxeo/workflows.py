# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Task, Workflow
from .utils import SwapAttr


class API(APIEndpoint):
    def __init__(self, client, endpoint='workflow', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Workflow, headers=headers)

    def get(self, workflow_id=None):
        # type: (Optional[Text]) -> Workflow
        """
        Get the detail of a workflow.

        :param workflow_id: the id of the workflow
        :return: the workflow
        """
        return super(API, self).get(path=workflow_id)

    def post(self, model, document=None, options=None):
        # type: (Text, Document, Optional[Dict[Text, Any]]) -> Workflow
        """
        Start a workflow.

        :param model: the workflow to start
        :param document: the document to start the workflow on
        :param options: options for the workflow
        :return: the created workflow
        """
        data = {
            'workflowModelName': model,
            'entity-type': 'workflow'
        }
        options = options or {}
        if 'attachedDocumentIds' in options:
            data['attachedDocumentIds'] = options['attachedDocumentIds']
        if 'variables' in options:
            data['variables'] = options['variables']

        if document:
            path = 'id/{}/@workflow'.format(document.uid)
            with SwapAttr(self, 'endpoint', self.client.api_path):
                workflow = super(API, self).post(data, path=path)
        else:
            workflow = super(API, self).post(data)
        return workflow

    start = post  # Alias for clarity

    def put(self, **kwargs):
        raise NotImplementedError

    def delete(self, workflow_id):
        # type: (Text) -> Workflow
        """
        Delete a workflow.

        :param workflow_id: the id of the workflow to delete
        :return: the deleted workflow
        """
        return super(API, self).delete(workflow_id)

    def graph(self, workflow):
        # type: (Text) -> Dict[Text, Any]
        """
        Get the graph of the workflow in JSON format.

        :param workflow: the worklow to get the graph from
        :return: the graph
        """
        request_path = '{}/graph'.format(workflow.uid)
        return super(API, self).get(path=request_path)

    def of(self, document):
        # type: (Document) -> Union[Workflow, List[Workflow]]
        """
        Get the workflows of a document.

        :param document: the document
        :return: the corresponding workflows
        """
        path = 'id/{}/@workflow'.format(document.uid)

        with SwapAttr(self, 'endpoint', self.client.api_path):
            workflows = super(API, self).get(path=path)
        return workflows

    def started(self, model):
        # type: (Text) -> List[Workflow]
        """
        Get started workflows having the specified model.

        :param model: the workflow model
        :return: the started workflows
        """
        return super(API, self).get(params={'workflowModelName': model})

    def tasks(self, options=None):
        # type: (Optional[Dict[Text, Text]]) -> List[Task]
        """
        Get a list of tasks following the (optional) constraints.

        :param options: the options
        :return: the corresponding list of tasks
        """
        endpoint = '{}/task'.format(self.client.api_path)
        with SwapAttr(self, 'endpoint', endpoint):
            tasks = super(API, self).get(cls=Task, params=options)
        return tasks
