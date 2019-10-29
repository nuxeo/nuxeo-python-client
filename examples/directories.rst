Work with directories
---------------------

**Fetch entries of a directory**

The number of returned entries is configured by the
`querySizeLimit <https://github.com/nuxeo/nuxeo/blob/82d03282c7ab8cd37c87f991161e4b39eed08ec0/nuxeo-distribution/nuxeo-nxr-server/src/main/resources/templates/common/config/default-directories-bundle.xml#L23>`__
parameter on the server (50 by default).

.. code:: python

    entries = nuxeo.directories.get('nature').entries

**Fetch only 10 entries of a directory**

.. code:: python

    entries = nuxeo.directories.get('nature', pageSize=10).entries

**Fetch only 10 entries of the 2nd page of a directory**

The ``currentPageIndex`` starts at 0, so to fetch the 2nd page, we use the value ``1``.

.. code:: python

    entries = nuxeo.directories.get('nature', pageSize=10, currentPageIndex=1).entries

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
