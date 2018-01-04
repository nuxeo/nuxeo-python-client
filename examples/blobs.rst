Work with blobs
---------------

**Add a Blob to a file**

.. code:: python

    from nuxeo.models import Document, FileBlob

    # Create a file
    new_file = Document(
        name='foo',
        type='File',
        properties={
            'dc:title': 'foo',
        })
    file = nuxeo.documents.create(new_file, parent_path='/')

    # Create and upload a blob
    blob = FileBlob('/path/to/file')
    uploaded = nuxeo.uploads.upload(blob)

    # Attach it to the file
    operation = nuxeo.operations.new('Blob.AttachOnDocument')
    operation.params = {'document': '/foo'}
    operation.input_obj = uploaded
    operation.execute()


