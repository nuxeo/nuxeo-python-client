Authentication
--------------

Basic
=====

.. code:: python

    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = ("alice", "password")
    server = Nuxeo(host=host, auth=auth)


JSON Web Token
==============

.. code:: python

    from nuxeo.auth import JWTAuth
    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = JWTAuth("token")
    server = Nuxeo(host=host, auth=auth)


OAuth2
======

OAuth2 with automatic credentials renewal is available by default.

The ``OAuth2`` class can take several optionnal keyword arguments:

- ``authorization_endpoint``: custom authorization endpoint
- ``client_id``: the consumer client ID
- ``client_secret``: the consumer client secret
- ``openid_configuration_url``: configuration URL for OpenID Connect Discovery
- ``redirect_uri``: the redirect URI (mandatory when using ADFS ofr instance)
- ``token``: existent token
- ``token_endpoint``: custom token endpoint

When ``openid_configuration_url`` is passed, ``authorization_endpoint`` and ``token_endpoint`` have no effect.

Scenario 1: Generating a New Token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from nuxeo.auth import OAuth2
    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    nuxeo = Nuxeo(host=host)
    nuxeo.client.auth = OAuth2(
        nuxeo.client.host, client_id="<client-id>", client_secret="<client-secret>"
    )

    # Step 1, generate the auth URL
    # (*state* and *code_verifier* should be used by the caller to validate the request)
    uri, state, code_verifier = nuxeo.client.auth.create_authorization_url()

    # Step 2, ask the user to open *uri* in their browser (here we are emulating such action)
    req = requests.get(uri, auth=("Administrator", "Administrator"))
    authorization_response = req.url

    # Step 3, get the token
    token = nuxeo.client.auth.request_token(
        code_verifier=code_verifier,
        authorization_response=authorization_response,
    )

    # Step 3, another possibility when you already parsed *authorization_response* and know the *code*
    token = nuxeo.client.auth.request_token(
        code_verifier=code_verifier,
        code=code,
        state=state,
    )


Scenario 2: Using an Existing Token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from nuxeo.auth import OAuth2
    from nuxeo.client import Nuxeo

    # Token saved that we want to reuse
    token = {
        "access_token": "...",
        "refresh_token": "...",
        "token_type": "bearer",
        "expires_in": 3599,
        "expires_at": 1618242664,
    }
    host = "https://<HOST>/nuxeo/"
    nuxeo = Nuxeo(host=host)
    nuxeo.client.auth = OAuth2(
        nuxeo.client.host, client_id="<client-id>", client_secret="<client-secret>", token=token
    )


Portal SSO
==========

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


Token
=====

.. code:: python

    from nuxeo.auth import TokenAuth
    from nuxeo.client import Nuxeo

    host = "https://<HOST>/nuxeo/"
    auth = TokenAuth("token")
    server = Nuxeo(host=host, auth=auth)
