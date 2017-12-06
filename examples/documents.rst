Work with documents
-------------------

**Create a Repository object**

.. code:: python

    default_repository = nuxeo.repository()  # 'default' repository
    test_repository = nuxeo.repository('test')  # 'test' repository

Manipulate documents
~~~~~~~~~~~~~~~~~~~~

**Fetch the Root document**

.. code:: python

    nuxeo.repository().fetch('/')

**Create a new workspace**

.. code:: python

    new_ws = {
        'entity-type': 'document',
        'name': 'ws',
        'type': 'Workspace',
        'properties': {
            'dc:title': 'ws',
        }
    }
    ws = nuxeo.repository().create('/', new_ws)

**Create a new folder**

.. code:: python

    new_folder = {
        'entity-type': 'document',
        'name': 'a-folder',
        'type': 'Folder',
        'properties': {
            'dc:title': 'foo',
        }
    }
    folder = nuxeo.repository().create('/ws', new_folder)

**Modify a document**

.. code:: python

    doc = nuxeo.repository().fetch('/a-folder')
    doc.set({'dc:title': 'bar'})
    doc.save()

**Delete a document**

.. code:: python

    nuxeo.repository().delete('/a-folder')

**Get a document property**

.. code:: python

    doc.get('dc:title')

**Fetch the main Blob of a document**

.. code:: python

    doc.fetch_blob()

**Convert a document main Blob to PDF**

.. code:: python

    doc.convert({'format': 'pdf'})

**Fetch the ‘thumbnail’ rendition**

.. code:: python

    doc.fetch_rendition('thumbnail')

**Fetch the ACLs**

.. code:: python

    doc.fetch_acls()~

Use workflows and tasks
~~~~~~~~~~~~~~~~~~~~~~~

**Start a workflow**

.. code:: python

    doc.start_workflow('SerialDocumentReview')

**Complete a workflow task**

.. code:: python

    task = workflow.fetch_tasks()
    variables = {
        'participants': ['user:Administrator'],
        'assignees': ['user:Administrator'],
        'end_date':'2011-10-23T12:00:00.00Z'
    }
    task.complete('start_review', variables, comment='a comment')


Permissions and locks
~~~~~~~~~~~~~~~~~~~~~

**Add a permission**

.. code:: python

    doc.add_permission({'username': 'test', 'permission': 'Write'})

**Remove a permission**

.. code:: python

    doc.remove_permission({'id': 'members:Write:true:Administrator::'})

**Check for a permission**

.. code:: python

    doc.has_permission('Write')

**Lock document**

.. code:: python

    doc.lock()

**Unlock document**

.. code:: python

    doc.unlock()

**Fetch Lock Status**

.. code:: python

    doc.fetch_lock_status()
