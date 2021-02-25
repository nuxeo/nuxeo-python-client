Authentication
--------------

Basic Authentication
====================

.. code:: python

    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = ("alice", "password")
    server = Nuxeo(host=host, auth=auth)


Portal SSO Authentication
=========================

.. code:: python

    from nuxeo.auth import PortalSSOAuth
    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = PortalSSOAuth("alice", "secret")
    server = Nuxeo(host=host, auth=auth)

If the server is configured to use a digest algorithm different than ``MD5``, you can tell the client like:

.. code:: python

    # Example when the server is configured to use SHA256:
    auth = PortalSSOAuth("alice", "secret", digest_algorithm="sha256")


Token Authentication
====================

.. code:: python

    from nuxeo.auth import TokenAuth
    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = TokenAuth("token")
    server = Nuxeo(host=host, auth=auth)
