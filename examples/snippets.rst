Useful snippets
---------------

**Prevent an operation from sending back data**

If you want to perform an operation and don't care about
getting data back (for example, attaching a blob to a document
returns the blob, you might not want to download that big file),
you need to set ``void_op`` to True which will add the
right request header for you, and you'll just get the status back.

.. code:: python

    operation = nuxeo.operation('Blob.AttachOnDocument')
    operation.params({'document':'/foo'})
    operation.input(uploaded)
    res = operation.execute(void_op=True)  # res will have no content


**Enable Drive synchronization on a folder**

This example enables the synchronization of a folder through
Nuxeo Drive, but you can also run it on an entire Workspace.

.. code:: python

    operation = nuxeo.operation('NuxeoDrive.SetSynchronization')
    operation.params({
        'enable': True
    })
    operation.input('/My Folder')
    operation.execute()

**Log something on the server**

.. code:: python

    operation = nuxeo.operation('Log')
    operation.params({
        'level': 'info',
        'message': 'This is a log message'
    })
    operation.execute()

**Query the audit log**

If you want to retrieve the audit logs starting from a specific
``lowerBound`` event id, you can query the audit system like this:

.. code:: python

    query = 'from LogEntry log where log.eventId >= '
    query += lowerBound
    query += ' order by log.eventDate DESC'

    operation = nuxeo.operation('Audit.Query')
    operation.params({
        'query': query
    })
    results = operation.execute()
