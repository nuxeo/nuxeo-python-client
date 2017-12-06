Work with blobs
---------------

**Add a Blob to a file**

.. code:: python

    from nuxeo.blob import FileBlob

    # Create a file
    new_file = {
        'entity-type': 'document',
        'name': 'foo',
        'type': 'File',
        'properties': {
            'dc:title': 'foo',
        }
    }
    file = nuxeo.repository().create('/', new_file)

    # Create and upload a blob
    blob = FileBlob('/path/to/file')
    uploaded = nuxeo.batch_upload().upload(blob)

    # Attach it to the file
    operation = nuxeo.operation('Blob.AttachOnDocument')
    operation.params({'document':'/foo'})
    operation.input(uploaded)
    operation.execute()


