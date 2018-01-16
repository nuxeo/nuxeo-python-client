Work with blobs
---------------

**Add a Blob to a file**

When uploading a blob, you can choose to do a chunked upload
by passing ``chunked=True`` to the upload method. If the file
is too big it will be chunked automatically even without this
argument. An interrupted chunked upload can be resumed by
relaunching the upload command with the same batch and blob.

.. code:: python

    from nuxeo.models import Document, FileBlob
    from nuxeo.exceptions import UploadError

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
    try:
        uploaded = nuxeo.uploads.upload(blob, chunked=True)
    except UploadError:
        # The blob wasn't uploaded despite the 3 retries,
        # you can handle it however you like and relaunch
        # the same command

    # Attach it to the file
    operation = nuxeo.operations.new('Blob.AttachOnDocument')
    operation.params = {'document': '/foo'}
    operation.input_obj = uploaded
    operation.execute()


