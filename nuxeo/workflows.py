# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Workflow
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text, Union  # noqa
        from .client import NuxeoClient  # noqa
        from .models import Document, Task  # noqa
        from .tasks import API as TasksAPI  # noqa
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for workflows. """
    def __init__(
        self,
        client,  # type: NuxeoClient
        tasks,  # type: TasksAPI
        endpoint='workflow',  # type: Text
        headers=None  # type: Optional[Dict[Text, Text]]
    ):
        # type: (...) -> None
        self.tasks_api = tasks
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

    def post(
        self,
        model,  # type: Text
        document=None,  # type: Optional[Document]
        options=None,  # type: Optional[Dict[Text, Any]]
    ):
        # type: (...) -> Workflow
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
        # type: (Any) -> None
        raise NotImplementedError()

    def delete(self, workflow_id):
        # type: (Text) -> None
        """
        Delete a workflow.

        :param workflow_id: the id of the workflow to delete
        """
        super(API, self).delete(workflow_id)

    def graph(self, workflow):
        # type: (Workflow) -> Dict[Text, Any]
        """
        Get the graph of the workflow in JSON format.

        :param workflow: the worklow to get the graph from
        :return: the graph
        """
        request_path = '{}/graph'.format(workflow.uid)
        return super(API, self).get(path=request_path)

    def started(self, model):
        # type: (Text) -> List[Workflow]
        """
        Get started workflows having the specified model.

        :param model: the workflow model
        :return: the started workflows
        """
        return super(API, self).get(params={'workflowModelName': model})

    def tasks(self, workflow):
        # type: (Workflow) -> List[Task]
        """ Get the tasks of a workflow. """
        return self.tasks_api.get(workflow.as_dict())
