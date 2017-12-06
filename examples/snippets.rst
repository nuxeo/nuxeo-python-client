Useful snippets
---------------

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
