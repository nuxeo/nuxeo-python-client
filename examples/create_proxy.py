# coding: utf-8
"""
Full example on how to create a live proxy with the Nuxeo Python Client module.
To install it:
    pip install nuxeo
"""

from nuxeo.client import Nuxeo
from nuxeo.models import Document


def main():

    # Connection
    host = 'http://127.0.0.1:8080/nuxeo/'
    auth = ('Administrator', 'Administrator')
    nuxeo = Nuxeo(host=host, auth=auth)

    # Create a workspace
    new_ws = Document(
        name='Tests',
        type='Workspace',
        properties={
            'dc:title': 'Tests',
        })
    workspace = nuxeo.documents.create(new_ws, parent_path='/default-domain/workspaces')
    print(workspace)

    # Create a document
    operation = nuxeo.operations.new('Document.Create')
    operation.params = {
        'type': 'File',
        'name': 'foo.txt',
        'properties': {'dc:title': 'foo.txt', 'dc:description': 'bar'}
    }
    operation.input_obj = '/'
    doc = operation.execute()
    print(doc)

    # Create a proxy live
    operation = nuxeo.operations.new('Document.CreateLiveProxy')
    operation.params = {
        # NOTICE - ATTENTION
        # CREATE A WORKSPACE AS default-domain/workspaces/ws
        'Destination Path': '/default-domain/workspaces/ws',
    }
    operation.input_obj = '/{}'.format(doc['title'])
    proxy = operation.execute()
    print(proxy)

    entry = nuxeo.documents.get(uid=proxy['uid'])
    print(entry.type)


if __name__ == '__main__':
    exit(main())
