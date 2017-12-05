Client Library for Nuxeo API
----------------------------

|Build Status|

The Nuxeo Python Client is a Python client library for the Nuxeo
Automation and REST API.

This is an on-going project, supported by Nuxeo.

Getting Started
---------------

The installation is as simple as:

::

    $ pip install --upgrade nuxeo

Then, use the following ``import`` statement to have access to the Nuxeo
API:

.. code:: python

    from nuxeo import Nuxeo

Documentation
-------------

Check out the `API documentation <https://nuxeo.github.io/nuxeo-python-client/latest/>`__.

Requirements
------------

The Nuxeo Python client works only with Nuxeo Platform >= LTS 2015.

Quick Start
-----------

This quick start guide will show how to do basics operations using the
client.

Creating a Client
~~~~~~~~~~~~~~~~~

.. code:: python

    nuxeo = Nuxeo(
      auth={
        'username': 'Administrator',
        'password': 'Administrator'
      })

To connect to a different Nuxeo Platform Instance, you can use the
following:

.. code:: python

    nuxeo = Nuxeo(
      base_url='http://demo.nuxeo.com/nuxeo/',
      auth={
        'username': 'Administrator',
        'password': 'Administrator'
      })

Operation
~~~~~~~~~

``Operation`` object allows you to execute an operation (or operation
chain).

See the
`Operation <http://nuxeo.github.io/nuxeo-python-client/latest/#module-nuxeo.operation>`__
documentation.

Samples
^^^^^^^

**Call an operation to create a new folder in the Root document**

.. code:: python

    operation = nuxeo.operation('Document.Create')
    operation.params({
        'type': 'Folder',
        'name': 'My Folder',
        'properties': 'dc:title=My Folder \ndc:description=A Simple Folder'
      })
    operation.input('/')
    doc = operation.execute()

Request
~~~~~~~

The ``Request`` object allows you to call the Nuxeo REST API.

See the `Request <http://nuxeo.github.io/nuxeo-python-client/latest/>`__
documentation.

.. samples-1:

Samples
^^^^^^^

**Fetch the Administrator user**

.. code:: python

    user = nuxeo.request('user/Administrator')

**Fetch the whole list of Natures**

.. code:: python

    natures = nuxeo.request('directory/nature')

Repository
~~~~~~~~~~

The ``Repository`` object allows you to work with document.

See the
`Repository <http://nuxeo.github.io/nuxeo-python-client/latest/#module-nuxeo.repository>`__
documentation.

.. samples-2:

Samples
^^^^^^^

**Create a ``Repository`` object**

.. code:: python

    defaultRepository = nuxeo.repository(); // 'default' repository
    ...
    testRepository = nuxeo.repository('test'); // 'test' repository
    ...

**Fetch the Root document**

.. code:: python

    nuxeo.repository().fetch('/')

**Create a new folder**

.. code:: python

    newFolder = {
      'entity-type': 'document',
      'name': 'a-folder',
      'type': 'Folder',
      'properties': {
        'dc:title': 'foo',
      }
    }
    folder = nuxeo.repository().create('/', newFolder)

**Delete a document**

.. code:: javascript

    nuxeo.repository().delete('/a-folder')

Document
~~~~~~~~

``Repository`` object returns and works with ``Document`` objects.
``Document`` objects exposes a simpler API to work with a document.

See the
`Document <http://nuxeo.github.io/nuxeo-python-client/latest/#module-nuxeo.document>`__
documentation.

.. samples-3:

Samples
^^^^^^^

**Retrieve a ``Document`` object**

.. code:: python

    doc = nuxeo.repository().fetch('/')

**Set a document property**

.. code:: python

    doc.set({ 'dc:title': 'foo' })

**Get a document property**

.. code:: python

    doc.get('dc:title')

**Save an updated document**

.. code:: python

    doc = nuxeo.repository().fetch('/')
    doc.set({ 'dc:title': 'foo' })
    doc.save()

**Fetch the main Blob of a document**

.. code:: python

    doc.fetch_blob()

**Convert a document main Blob to PDF**

.. code:: python

    doc.convert({ 'format': 'pdf' })

**Fetch the ‘thumbnail’ rendition**

.. code:: python

    doc.fetch_rendition('thumbnail')

**Fetch the ACLs**

.. code:: python

    doc.fetch_acls()

**Add permission**

.. code:: python

    doc.add_permission({'username': 'test', 'permission': 'Write'})

**Remove permission**

.. code:: python

    doc.remove_permission({'id': 'members:Write:true:Administrator::'})

**Has permission**

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

**Start a workflow**

.. code:: python

    doc.start_workflow('SerialDocumentReview')

**Complete a workflow task**

.. code:: javascript

    task = workflow.fetch_tasks()
    variables = {'participants':['user:Administrator'],'assignees':['user:Administrator'], 'end_date':'2011-10-23T12:00:00.00Z'};
    task.complete('start_review', variables, comment='a comment');

BatchUpload
~~~~~~~~~~~

The ``BatchUpload`` object allows you to upload blobs to a Nuxeo
Platform instance, and use them as operation input or as document
property value.

See the
`BatchUpload <http://nuxeo.github.io/nuxeo-python-client/latest/#batchupload>`__
documentation.

.. samples-4:

Samples
^^^^^^^

**Create a Nuxeo.Blob to be uploaded**

.. code:: python

    from nuxeo.blob import FileBlob
    from nuxeo.blob import BufferBlob
    BufferBlob('Content of this text', 'Test.txt', 'text/plain')
    ...
    FileBlob('/path/to/file)

**Upload a blob**

.. code:: python

    nuxeo.batch_upload().upload(blob)

**Attach an uploaded blob to a document**

.. code:: python

    uploaded = nuxeo.batch_upload().upload(blob)
    operation = nuxeo.operation('Blob.AttachOnDocument')
    operation.params({'document':'/a-file'})
    operation.input(uploaded)
    operation.execute()

Users
~~~~~

The ``Users`` object allows you to work with users.

See the
`Users <http://nuxeo.github.io/nuxeo-python-client/latest/#module-nuxeo.users>`__
documentation.

.. samples-5:

Samples
^^^^^^^

**Fetch an user**

.. code:: pyton

    nuxeo.users().fetch('Administrator')

**Create a new user**

.. code:: python

    newUser = {
        'username': 'leela',
        'firstName': 'Leela',
        'company': 'Futurama',
        'email': 'leela@futurama.com',
      }
    user = nuxeo.users().create(newUser)

**Delete an user**

.. code:: python

    nuxeo.users().delete('leela')

Groups
~~~~~~

The ``Groups`` object allows you to work with groups.

See the
`Groups <http://nuxeo.github.io/nuxeo-python-client/latest/#module-nuxeo.groups>`__
documentation.

.. samples-6:

Samples
^^^^^^^

**Fetch a group**

.. code:: python

    nuxeo.groups().fetch('administrators')

**Create a new group**

.. code:: python

    newGroup = {
      'groupname': 'foo',
      'grouplabel': 'Foo',
    }
    group = nuxeo.groups().create(newGroup)

**Delete a group**

.. code:: python

    nuxeo.groups().delete('foo')

Directory
~~~~~~~~~

The ``Directory`` object allows you to work with directories.

See the
`Directory <http://nuxeo.github.io/nuxeo-python-client/latest/#module-nuxeo.directory>`__
documentation.

.. samples-7:

Samples
^^^^^^^

**Fetch all entries of a directory**

.. code:: python

    entries = nuxeo.directory('nature').fetch_all()

**Fetch a given directory entry**

.. code:: python

    entry = nuxeo.directory('nature').fetch('article')

**Create a new directory entry**

.. code:: python

    newEntry = {
      'id': 'foo',
      'label': 'Foo',
    }
    entry = nuxeo.directory('nature').create(newEntry)

**Delete a directory entry**

.. code:: python

    nuxeo.directory('nature').delete('foo')

Contributing
------------

See our `contribution documentation <https://doc.nuxeo.com/x/VIZH>`__.

.. requirements-1:

Requirements
~~~~~~~~~~~~

-  `Python >= 2.7 <https://www.python.org/downloads/>`__

Setup
~~~~~

::

    $ git clone https://github.com/nuxeo/nuxeo-python-client
    $ cd nuxeo-python-client
    $ python setup.py develop

Test
~~~~

A Nuxeo Platform instance needs to be running on
``http://localhost:8080/nuxeo`` for the tests to be run, and then:

::

    $ python setup.py test

Tests can be launched without a server with Maven and pytest:

::

    $ mvn -f ftest/pom.xml clean verify

Reporting Issues
~~~~~~~~~~~~~~~~

You can follow the developments in the Nuxeo Python Client project of
our JIRA bug tracker: https://jira.nuxeo.com/browse/NXPY.

You can report issues on
`answers.nuxeo.com <http://answers.nuxeo.com>`__.

License
-------

`Apache License 2.0 <https://www.apache.org/licenses/LICENSE-2.0.txt>`__
Copyright (c) Nuxeo

About Nuxeo
-----------

Nuxeo dramatically improves how content-based applications are built,
managed and deployed, making customers more agile, innovative and
successful. Nuxeo provides a next generation, enterprise ready platform
for building traditional and cutting-edge content oriented applications.
Combining a powerful application development environment with SaaS-based
tools and a modular architecture, the Nuxeo Platform and Products
provide clear business value to some of the most recognizable brands
including Verizon, Electronic Arts, Sharp, FICO, the U.S. Navy, and
Boeing. Nuxeo is headquartered in New York and Paris. More information
is available at `www.nuxeo.com <http://www.nuxeo.com/>`__.

.. |Build Status| image:: https://qa.nuxeo.org/jenkins/buildStatus/icon?job=Client/nuxeo-python-client-master&style=flat
   :target: https://qa.nuxeo.org/jenkins/job/Client/job/nuxeo-python-client-master/
