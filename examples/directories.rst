Work with directories
---------------------

**Fetch all entries of a directory**

.. code:: python

    entries = nuxeo.directory('nature').fetch_all()

**Fetch a given directory entry**

.. code:: python

    entry = nuxeo.directory('nature').fetch('article')

**Create a new directory entry**

.. code:: python

    new_entry = {
      'id': 'foo',
      'label': 'Foo',
    }
    entry = nuxeo.directory('nature').create(new_entry)

**Delete a directory entry**

.. code:: python

    nuxeo.directory('nature').delete('foo')
