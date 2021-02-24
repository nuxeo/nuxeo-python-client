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


Token Authentication
====================

.. code:: python

    from nuxeo.auth import TokenAuth
    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = TokenAuth("token")
    server = Nuxeo(host=host, auth=auth)
