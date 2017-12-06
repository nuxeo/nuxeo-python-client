# coding: utf-8
""" Tests with the Nuxeo Python client.
        pip install nuxeo-python-client
"""


def main():
    from nuxeo.nuxeo import Nuxeo

    # Connection
    base_url = 'http://127.0.0.1:8080/nuxeo/'
    auth = {'username': 'Administrator', 'password': 'Administrator'}
    nuxeo = Nuxeo(base_url=base_url, auth=auth)

    # Create a workspace
    new_ws = {
        'entity-type': 'Document',
        'name': 'Tests',
        'type': 'Workspace',
        'properties': {
            'dc:title': 'Tests',
        }
    }
    workspace = nuxeo.repository().create('/default-domain/workspaces', new_ws)
    print(workspace)

    # Create a document
    operation = nuxeo.operation('Document.Create')
    operation.params({
        'type': 'File',
        'name': 'foo.txt',
        'properties': {'dc:title': 'foo.txt', 'dc:description': 'bar'}
    })
    operation.input('/')
    doc = operation.execute()
    print(doc)

    # Create a proxy live
    operation = nuxeo.operation('Document.CreateLiveProxy')
    operation.params({
        # NOTICE - ATTENTION
        # CREATE A WORKSPACE AS default-domain/workspaces/ws
        'Destination Path': '/default-domain/workspaces/ws',
    })
    operation.input('/' + doc['title'])
    proxy = operation.execute()
    print(proxy)

    entry = nuxeo.repository().fetch(proxy['uid'])
    print(entry.type)


if __name__ == '__main__':
    exit(main())