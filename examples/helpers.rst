Helpers
-------

**Check the server access**

Whenever you want to check if the Nuxeo Platform server is reachable,
you can run this command. It will return a ``boolean`` representing the
availability of the server.

.. code:: python

    is_reachable = nuxeo.client.is_reachable()


**Get the Nuxeo Drive configuration**

You can fetch the Drive configuration from the server:

.. code:: python

    config = nuxeo.client.request('GET', 'drive/configuration', default={})

If it has been filled, ``config`` will have the following structure:

.. code:: python

    {
        'log_level_file': 'DEBUG',
        'ignored_suffixes': ['.bak', '.crdownload', '.lock', '.nxpart', '.part', '.partial', '.swp', '.tmp', '~', '.dwl', '.dwl2'],
        'ignored_files': ['^atmp\\d+$'],
        'update_check_delay': 3600,
        'delay': 30,
        'ui': 'web',
        'beta_channel': False,
        'timeout': 30,
        'ignored_prefixes': ['.', 'icon\r', 'thumbs.db', 'desktop.ini', '~$'],
        'handshake_timeout': 60
    }

**Get available operations**

You can search for available operations on the
`explorer <http://explorer.nuxeo.com/nuxeo/site/distribution/>`__
(click on `Search Operations` on the version corresponding
to your Nuxeo Platform).
You can also run the following bit of code to see the list:

.. code:: python

    import json
    ops = nuxeo.operations.operations.keys()
    ops.sort()
    json.dumps(ops)

You'll get an output like this:

.. code:: json

    [
        "Actions.GET",
        "AddEntryToMultivaluedProperty",
        "AttachFiles",
        "Audit.Log",
        "Audit.LogEvent",
        ...
    ]

And if you pick one you can see its definition:

.. code:: python

    json.dumps(nuxeo.operations.operations['Log'])

With an output like this:

.. code:: json

    {
        "category": "Notification",
        "description": "Logging with log4j",
        "url": "Log",
        "label": "Log",
        "params": [
            {
                "widget": "Option",
                "name": "level",
                "required": true,
                "values": ["info", "debug", "warn", "error"],
                "type": "string",
                "order": 0,
                "description": ""
            },
            {
                "widget": null,
                "name": "message",
                "required": true,
                "values": [],
                "type": "string",
                "order": 0,
                "description": ""
            },
            {
                "widget": null,
                "name": "category",
                "required": false,
                "values": [],
                "type": "string",
                "order": 0,
                "description": ""
            }
        ],
        "signature": [
            "void",
            "void"
        ],
        "requires": null,
        "id": "Log",
        "aliases": ["LogOperation"]
    }

**Check operation parameters**

When you execute an operation, the name of the operation and
the parameters you chose will be checked by the ``nuxeo.operations.check_params()``
method. If you want to check the parameters of your operation by
yourself before running it, you can use the following:

.. code:: python

    from nuxeo.exceptions import BadQuery

    try:
        nuxeo.operations.check_params(
            'Log', {'level': 'info',
                    'message': 'I am logging something'})
    except BadQuery as e:
        print(e)  # Indicates what is wrong
    else:
        # The parameters are valid
