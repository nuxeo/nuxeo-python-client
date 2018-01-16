# coding: utf-8
from __future__ import unicode_literals

from .endpoint import APIEndpoint
from .models import Workflow
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text, Union
        from .client import NuxeoClient
        from .models import Document
except ImportError:
    pass


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
        # type: (Workflow) -> Dict[Text, Any]
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
