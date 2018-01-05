Work with directories
---------------------

**Fetch all entries of a directory**

.. code:: python

    entries = nuxeo.directories.get('nature').entries

**Fetch a given directory entry**

.. code:: python

    entry = nuxeo.directories.get('nature', 'article')

**Create a new directory entry**

.. code:: python

    new_entry = DirectoryEntry(
        properties={
          'id': 'foo',
          'label': 'Foo',
        })
    entry = nuxeo.directories.get('nature').create(new_entry)

**Delete a directory entry**

.. code:: python

    nuxeo.directories.get('nature').delete('foo')
