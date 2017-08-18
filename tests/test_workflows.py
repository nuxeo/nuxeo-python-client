# coding: utf-8
from .common import NuxeoTest


class WorkflowTest(NuxeoTest):

    def setUp(self):
        super(WorkflowTest, self).setUp()
        self._clean_root()
        try:
            self.repository.delete('/task-root')
            self.repository.delete('/document-route-instances-root')
        except:
            pass
        self._workflows = self.nuxeo.workflows()

    def test_get_workflows(self):
        workflow = self._workflows.start('SerialDocumentReview')
        self.assertIsNotNone(workflow)
        wfs = self._workflows.fetch_started_workflows('SerialDocumentReview')
        self.assertEqual(len(wfs), 1)
        tasks = self._workflows.fetch_tasks()
        self.assertEqual(len(tasks), 1)
        tasks = self._workflows.fetch_tasks({'workflowInstanceId': wfs[0].get_id()})
        self.assertEqual(len(tasks), 1)
        tasks = self._workflows.fetch_tasks({'workflowInstanceId': 'unknown'})
        self.assertEqual(len(tasks), 0)
        tasks = self._workflows.fetch_tasks({'workflowInstanceId': wfs[0].get_id(), 'userId': 'Administrator'})
        self.assertEqual(len(tasks), 1)
        tasks = self._workflows.fetch_tasks({'workflowInstanceId': wfs[0].get_id(), 'userId': 'Georges Abitbol'})
        self.assertEqual(len(tasks), 0)
        tasks = self._workflows.fetch_tasks({'workflowInstanceId': wfs[0].get_id(), 'workflowModelName': 'SerialDocumentReview'})
        self.assertEqual(len(tasks), 1)
        tasks = self._workflows.fetch_tasks({'workflowModelName': 'foo'})
        self.assertEqual(len(tasks), 0)

    def test_fetch_graph(self):
        workflow = self._workflows.start('SerialDocumentReview')
        self.assertIsNotNone(workflow)
        wfs = self._workflows.fetch_started_workflows('SerialDocumentReview')
        self.assertEqual(len(wfs), 1)
        workflow = wfs[0]
        graph = workflow.fetch_graph()
        self.assertIsNotNone(graph)

    def test_basic_workflow(self):
        doc = self._create_blob_file()
        workflow = doc.start_workflow('SerialDocumentReview')
        self.assertIsNotNone(workflow)
        wfs = self._workflows.fetch_started_workflows('SerialDocumentReview')
        self.assertEqual(len(wfs), 1)
        tasks = self._workflows.fetch_tasks()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        vars = {'participants':['user:Administrator'], 'assignees':['user:Administrator'], 'end_date': '2011-10-23T12:00:00.00Z'};
        task.complete('start_review', vars, comment='a comment')
        workflows = doc.fetch_workflows()
        self.assertEqual(len(workflows), 1)
        self.assertEqual(task.state, 'ended')
        tasks = workflow.fetch_tasks()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        task.complete('validate', {'comment': 'a comment'})
        self.assertEqual(task.state, 'ended')
        workflows = doc.fetch_workflows()
        self.assertEqual(len(workflows), 0)