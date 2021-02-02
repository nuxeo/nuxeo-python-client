Client Library for Nuxeo API
----------------------------

|Build Status| |Quality|

The Nuxeo Python Client is a Python client library for the Nuxeo
Automation and REST API. It works with both Python 2.7 and 3.5+.

This is an ongoing project, supported by Nuxeo.

Getting Started
---------------

The installation is as simple as:

.. code:: shell

    python -m pip install -U --user nuxeo

The client can make use of the Amazon S3 provider, to install its requirements:

.. code:: shell

    python -m pip install -U --user nuxeo[s3]

Import
------

Then, use the following ``import`` statement to have access to the Nuxeo
API:

.. code:: python

    from nuxeo.client import Nuxeo

Documentation
-------------

Check out the `API documentation <https://nuxeo.github.io/nuxeo-python-client/latest/>`__.

Requirements
------------

The Nuxeo Python client works only with:

-  the Nuxeo Platform >= LTS 2015
-  ``requests`` >= 2.12.2 (for unicode authentication)
-  ``setuptools`` >= 30.3.0

Quick Start
-----------

This quick start guide will show how to do basics operations using the
client.

Connect to the Nuxeo Platform
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to connect to the Nuxeo Platform with a basic authentication
is passing a tuple containing the ``username`` and the ``password`` to the
client, like so:

.. code:: python

    nuxeo = Nuxeo(auth=('Administrator', 'Administrator'))


You can then use the ``nuxeo`` object to interact with the Platform. If you want
to use a specific instance, you can specify the ``base_url`` like so:

.. code:: python

    nuxeo = Nuxeo(
        host='http://demo.nuxeo.com/nuxeo/',
        auth=('Administrator', 'Administrator')
    )

Download/Upload Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the `nuxeo/constants.py <nuxeo/constants.py>`__ file, you have several constants that are
used throughout the client that you can change to fit your needs. Some of them are:

-  ``CHECK_PARAMS`` (False by default), to check operation's parameters for each and every HTTP calls.
-  ``CHUNK_LIMIT`` (10 MiB by default), the size above which the upload will automatically be chunked.
-  ``CHUNK_SIZE`` (8 KiB by default), the size of the chunks when downloading.
-  ``MAX_RETRY`` (5 by default), the number of retries for connection error on any HTTP call.
-  ``UPLOAD_CHUNK_SIZE`` (20 MiB by default), the size of the chunks when uploading.


Run NXQL Queries
~~~~~~~~~~~~~~~~

You can run queries in NXQL (NXQL is a subset of SQL,
you can check how to use it `in the documentation <https://doc.nuxeo.com/nxdoc/nxql/>`__).
Here, we are first `fetching a workspace <documents.rst>`__, and then using its
``uid`` to build a query which will find all its children that have a ``File``
or ``Picture`` type, and are not deleted.

.. code:: python

    # Fetch a workspace
    ws = nuxeo.documents.get(path='/default-domain/workspaces/ws')

    # Build a query using its UID
    nxql = ("SELECT * FROM Document WHERE ecm:ancestorId = '{uid}'"
            "   AND ecm:primaryType IN ('File', 'Picture')"
            "   AND ecm:currentLifeCycleState != 'deleted'")
    query = nxql.format(uid=ws.uid)

    # Make the request
    search = nuxeo.client.query(query, params={'properties': '*'})

    # Get results
    entries = search['entries']

``entries`` will be a ``list`` containing a ``dict`` for each
element returned by the query.

Usage
~~~~~

Now that your client is set up, here are pages to help you with the
main functions available:

-  `Manage users and groups <examples/users_and_groups.rst>`__
-  `Work with documents <examples/documents.rst>`__
-  `Work with directories <examples/directories.rst>`__
-  `Work with blobs <examples/blobs.rst>`__
-  `Work with comments <examples/comments.rst>`__
-  `Run requests <examples/requests.rst>`__
-  `Helpers <examples/helpers.rst>`__
-  `Useful snippets <examples/snippets.rst>`__
-  `Script: Find duplicates <examples/find_duplicates.py>`__
-  `Script: Create a live proxy <examples/create_proxy.py>`__

You can also check `the  API documentation <http://nuxeo.github.io/nuxeo-python-client/latest/>`__
of this Python client for further options.

Contributing
------------

See our `contribution documentation <https://doc.nuxeo.com/x/VIZH>`__.

Setup
~~~~~

.. code:: shell

    git clone https://github.com/nuxeo/nuxeo-python-client
    cd nuxeo-python-client
    python -m pip install -e ".[s3]"

Test
~~~~

A Nuxeo Platform instance needs to be running on
``http://localhost:8080/nuxeo`` for the tests to be run, and then:

.. code:: shell

    python -m pip install -U --user tox
    tox

Sentry
======

We use Sentry to catch unhandled errors from tests.
You can tweak it before running ``tox``.

It can be disabled:

.. code:: shell

    export SKIP_SENTRY=1

You can also customize the Sentry DSN for your own team:

.. code:: shell

    export SENTRY_DSN="XXX"

And customize the Sentry environment too:

.. code:: shell

    # Note that the default value is "testing"
    export SENTRY_ENV="testing"

Deploying
~~~~~~~~~

Releases are fully automated, have a look at that `GitHub Action <https://github.com/nuxeo/nuxeo-python-client/actions?query=workflow%3ARelease>`__.

Reporting Issues
~~~~~~~~~~~~~~~~

You can follow the developments in the Nuxeo Python Client project of
our JIRA bug tracker: `NXPY <https://jira.nuxeo.com/browse/NXPY>`__.

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

.. |Build Status| image:: https://github.com/nuxeo/nuxeo-python-client/workflows/Unit%20tests/badge.svg
   :target: https://github.com/nuxeo/nuxeo-python-client/actions?query=workflow%3A%22Unit+tests%22

.. |Quality| image:: https://github.com/nuxeo/nuxeo-python-client/workflows/Code%20quality/badge.svg
   :target: https://github.com/nuxeo/nuxeo-python-client/actions?query=workflow%3A%22Code+quality%22
