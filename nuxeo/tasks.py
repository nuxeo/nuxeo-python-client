# coding: utf-8
from __future__ import unicode_literals

from .compat import text
from .endpoint import APIEndpoint
from .models import Task


class API(APIEndpoint):
    def __init__(self, client, endpoint='task', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Task, headers=headers)

    def get(self, options=None):
        # type: (Optional[Text]) -> Union[Task, List[Task]]
        """
        Get tasks by id or by options.

        :param options: the id of the task or the constraints
        :return: the task(s)
        """
        params, request_path = None, None

        if isinstance(options, dict):
            params = options
        elif isinstance(options, text):
            request_path = options

        return super(API, self).get(request_path=request_path, params=params)

    def of(self, workflow):
        # type: (Workflow) -> Union[Task, List[Task]]
        """
        Get the tasks of a workflow.

        :param workflow: the workflow
        :return: the corresponding tasks
        """
        return self.get(workflow.as_dict())

    def post(self, task):
        raise NotImplementedError

    def put(self, task):
        # type: (Task) -> Task
        """
        Update a task.

        :param task: the task to update
        :return: the updated task
        """
        return super(API, self).put(task)

    def delete(self, task_id):
        raise NotImplementedError

    def complete(self, task, action, variables=None, comment=None):
        # type: (Task, Text, Optional[Dict[Text, Any]], Optional[Text]) -> Task
        """
        Complete the task.

        :param task: the task
        :param action: to take
        :param variables: to add to the Task
        :param comment: for the action
        :return: Updated task
        """
        task.comment = comment
        if variables:
            task.variables.update(variables)

        request_path = '{}/{}'.format(task.id, action)
        return super(API, self).put(task, request_path=request_path)

    def transfer(self, task, transfer, actors, comment=None):
        # type: (Text, Text, Text, Optional[Text]) -> None
        """
         Delegate or reassign the Task to someone else.

        :param task: the task to modify
        :param transfer: 'delegate' or 'reassign'
        :param actors: the actors involved
        :param comment: a comment
        :return:
        """
        if transfer == 'delegate':
            actors_type = 'delegatedActors'
        elif transfer == 'reassign':
            actors_type = 'actors'
        else:
            raise ValueError('Task tranfer must be either delegate or reassign.')

        params = {actors_type: actors}
        if comment:
            params['comment'] = comment

        request_path = '{}/{}'.format(task.id, transfer)
        super(API, self).put(None, request_path=request_path, params=params)
