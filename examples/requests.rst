Run requests
------------

With ``nuxeo.request(...)`` you can run any request you want
on the REST API. The following list of examples isn't exhaustive,
but you can search for available operations on the
`explorer <http://explorer.nuxeo.com/nuxeo/site/distribution/>`__
(click on `Search Operations` on the version corresponding
to your Nuxeo Platform).

**Fetch the Administrator user**

.. code:: python

    user = nuxeo.client.request('user/Administrator')

**Fetch the whole list of Natures**

.. code:: python

    natures = nuxeo.client.request('directory/nature')
