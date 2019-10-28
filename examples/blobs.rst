Work with blobs
---------------


Add a Blob to a Document
========================

When uploading a blob, you can choose to do a chunked upload
by passing ``chunked=True`` to the upload method. If the file
is too big (``> constants.CHUNK_LIMIT``) it will be chunked
automatically even without this argument. An interrupted
chunked upload can be resumed by relaunching the upload
command with the same batch and blob.

.. code:: python

    from nuxeo.models import Document, FileBlob
    from nuxeo.exceptions import UploadError

    # Create a file
    new_file = Document(
        name="foo",
        type="File",
        properties={
            "dc:title": "foo",
        })
    file = nuxeo.documents.create(new_file, parent_path="/")

    # Create a batch
    batch = nuxeo.uploads.batch()

    # Create and upload a blob
    blob = FileBlob("/path/to/file")
    try:
        uploaded = batch.upload(blob, chunked=True)
    except UploadError:
        # The blob wasn't uploaded despite the 3 retries,
        # you can handle it however you like and relaunch
        # the same command

    # Attach it to the file
    operation = nuxeo.operations.new("Blob.AttachOnDocument")
    operation.params = {"document": file.path}
    operation.input_obj = uploaded
    operation.execute()

Add Multiple Blobs to a Given Document
======================================

The snippet will create a document of type ``File`` and attach to it 3 text files.

.. code:: python

    from nuxeo.models import Document, FileBlob

    # Create a document
    new_file = Document(
        name="foo.txt",
        type="File",
        properties={
            "dc:title": "foo.txt",
        })
    file = nuxeo.documents.create(new_file, parent_path="/default-domain/workspaces")

    # Create a batch
    batch = nuxeo.uploads.batch()

    # Here, loop over files to upload
    for local_file in ("text1.txt", "text2.txt", "text3.txt"):
        # Create a blob
        blob = FileBlob(local_file)

        # Upload the blob in chunks
        batch.upload(blob, chunked=True)

    # Attach all blobs to the file
    batch.attach(file.path)

Advanced Upload
===============

If you are uploading a really big file, you might want to have more control over the upload.
For this purpose, you can use an ``Uploader`` object.

There are two ways to execute code in between the chunk uploads.
First, a callback can be passed to the uploader.
It is nice for small additions, maybe updating a variable or logging something, but cannot control the flow of the upload.

.. code:: python

    import logging
    from nuxeo.models import Document, FileBlob
    from nuxeo.exceptions import UploadError

    def log_progress(uploader):
        logging.info(f"Uploading part nº{uploader.index}")

    # Create a batch
    batch = nuxeo.uploads.batch()

    # Create and upload a blob
    blob = FileBlob("/path/to/file")

    uploader = batch.get_uploader(blob, chunked=True, callback=log_progress)
    try:
        uploader.upload()
    except UploadError:
        # Handle error

Otherwise, you can upload using a generator:

.. code:: python

    from nuxeo.models import Document, FileBlob
    from nuxeo.exceptions import UploadError

    # Create a batch
    batch = nuxeo.uploads.batch()

    # Create and upload a blob
    blob = FileBlob("/path/to/file")

    uploader = batch.get_uploader(blob, chunked=True)
    try:
        for _ in uploader.iter_upload():
            logging.info(f"Uploading part nº{uploader.index}")
    except UploadError:
        index = uploader.index
        chunk_count = uploader.chunk_count
        logging.info(f"Uploaded {index} chunks of {chunk_count} for file {uploader.blob.name}")

        # You can start from where it stopped by
        # calling uploader.upload(generate=True) again
