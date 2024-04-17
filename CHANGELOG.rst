Changelog
=========

6.1.2
-----

Release date: ``2024-xx-xx``

- `NXPY-254 <https://jira.nuxeo.com/browse/NXPY-254>`__: Authorization Error for OAuth
- `NXPY-253 <https://jira.nuxeo.com/browse/NXPY-253>`__: Restore capability to use the client with a local HTTP server
- `NXPY-255 <https://jira.nuxeo.com/browse/NXPY-255>`__: Fix Test cases for moto3
- `NXPY-258 <https://jira.nuxeo.com/browse/NXPY-258>`__: File download from aws S3 with auto-redirect not working in case of OAuth

Technical changes
-----------------

- Added ``verify`` to ``OAuth2`` to  turn off the certificate verification when using self signed certificates (values: True/ False).
- Added ``kwargs`` to ``OAuth2.refresh_token()`` to pass parameters (ex. ``verify``).
- Replaced mock_s3 with mock_aws in test_upload_s3.py

Minor changes
-----------------

- Upgraded `actions/checkout` from 3 to 4
- Upgraded `actions/download-artifact` from 3 to 4
- Upgraded `actions/upload-artifact` from 3 to 4
- Upgraded `actions/setup-python` from 4 to 5
- Upgraded `codecov/codecov-action` from 3.1.2 to 3.1.5
- Upgraded `pypa/gh-action-pypi-publish` from master to release/v1

6.1.1
-----

Release date: ``2023-11-23``

- `NXPY-243 <https://jira.nuxeo.com/browse/NXPY-243>`__: Python client fix testcase
- `NXPY-244 <https://jira.nuxeo.com/browse/NXPY-244>`__: Align Python Client with LTS 2023
- `NXPY-247 <https://jira.nuxeo.com/browse/NXPY-247>`__: Configure testcases
- `NXPY-248 <https://jira.nuxeo.com/browse/NXPY-248>`__: Remove sensitive information

Technical changes
-----------------

- Switched flake8 from gitlab to github
- Added F401 warning in ignore list for flake8

Minor changes
-----------------

- Upgraded `actions/download-artifact` from 2 to 3
- Upgraded `actions/upload-artifact` from 2 to 3
- Upgraded `actions/setup-python` from 2 to 4
- Upgraded `actions/checkout` from 2 to 3
- Upgraded `codecov/codecov-action` from 1 to 3.1.2


6.1.0
-----

Release date: ``2022-10-21``

- `NXPY-241 <https://jira.nuxeo.com/browse/NXPY-241>`__: Remove Support For Python 3.6
- `NXPY-240 <https://jira.nuxeo.com/browse/NXPY-240>`__: Upgrade Nuxeo Docker Image
- `NXPY-237 <https://jira.nuxeo.com/browse/NXPY-237>`__: Update Dependencies
- `NXPY-239 <https://jira.nuxeo.com/browse/NXPY-239>`__: Fix tests cases on Python
- `NXPY-238 <https://jira.nuxeo.com/browse/NXPY-239>`__: Fix issue with Self signed certificates

Technical changes
-----------------

- Added ``ssl_verify`` arguments

6.0.3
-----

Release date: ``2021-07-06``

- `NXPY-228 <https://jira.nuxeo.com/browse/NXPY-228>`__: Use proper job names in GitHub workflows
- `NXPY-230 <https://jira.nuxeo.com/browse/NXPY-230>`__: Allow to pass requests arguments to the OAuth2 client
- `NXPY-231 <https://jira.nuxeo.com/browse/NXPY-231>`__: Prevent warnings when packaging the module
- `NXPY-232 <https://jira.nuxeo.com/browse/NXPY-232>`__: Allow specifying the upload provider type in the batch details
- `NXPY-233 <https://jira.nuxeo.com/browse/NXPY-233>`__: Allow to pass additional arguments when querying document

Technical changes
-----------------

- Added ``subclient_kwargs`` keyword argument to ``OAuth2.__init__()``
- Added ``kwargs`` keyword arguments to nuxeo/documents.py::\ ``API.query()``

6.0.2
-----

Release date: ``2021-06-07``

- `NXPY-225 <https://jira.nuxeo.com/browse/NXPY-225>`__: Allow to pass additional arguments when asking for a ``batchId``

Technical changes
-----------------

- Added ``kwargs`` keyword arguments to nuxeo/uploads.py::\ ``API.post()``

6.0.1
-----

Release date: ``2021-05-18``

- `NXPY-223 <https://jira.nuxeo.com/browse/NXPY-223>`__: Fix third-party credentials renewal

6.0.0
-----

Release date: ``2021-05-10``

- `NXPY-129 <https://jira.nuxeo.com/browse/NXPY-129>`__: Drop support for Python 2.7 and 3.5

Technical changes
-----------------

- Removed compat.py

5.2.0
-----

Release date: ``2021-05-07``

- `NXPY-219 <https://jira.nuxeo.com/browse/NXPY-219>`__: Add support for OpenID Connect Discovery
- `NXPY-220 <https://jira.nuxeo.com/browse/NXPY-220>`__: Use a REST API call instead of Automation for ``Users.current_user()``

Technical changes
-----------------

- Added ``OAuth2.validate_access_token()``
- Added ``redirect_uri`` keyword argument to ``OAuth2.__init__()``
- Added ``openid_configuration_url`` keyword argument to ``OAuth2.__init__()``

5.1.0
-----

Release date: ``2021-04-27``

- `NXPY-201 <https://jira.nuxeo.com/browse/NXPY-201>`__: Implement support for OAuth2
- `NXPY-213 <https://jira.nuxeo.com/browse/NXPY-213>`__: Handle incomplete serialized HTTP error
- `NXPY-214 <https://jira.nuxeo.com/browse/NXPY-214>`__: Add a code coverage GitHub Action on PRs
- `NXPY-215 <https://jira.nuxeo.com/browse/NXPY-215>`__: Add support for the JSON Web Token authentication
- `NXPY-217 <https://jira.nuxeo.com/browse/NXPY-217>`__: Restore Python 2.7 support
- `NXPY-218 <https://jira.nuxeo.com/browse/NXPY-218>`__: Introduce the ``BasicAuth`` class

Technical changes
-----------------

- Added nuxeo/auth/basic.py
- Added nuxeo/auth/jwt.py
- Added nuxeo/auth/oauth2.py
- Added nuxeo/exceptions.py::\ ``OAuth2Error``
- Added nuxeo/utils.py::\ ``log_response()``

5.0.0
-----

Release date: ``2021-03-04``

- `NXPY-208 <https://jira.nuxeo.com/browse/NXPY-208>`__: Use ``__slots__`` for memory efficiency and attributes access velocity
- `NXPY-209 <https://jira.nuxeo.com/browse/NXPY-209>`__: Allow to pass a callback to ``uploads.refresh_token()``

Technical changes
-----------------

- Added ``token_callback`` keyword argument to ``Uploader.__init__()``
- Removed ``Task.comment``
- Removed ``User.password``. Use ``.change_password()`` instead.
- Added nuxeo/auth/base.py
- Added ``kwargs`` keyword arguments to nuxeo/uploads.py::\ ``API.get_uploader()``

4.1.1
-----

Release date: ``2021-02-26``

- `NXPY-203 <https://jira.nuxeo.com/browse/NXPY-203>`__: Better support badly cased or unknown Portal SSO digest algorithms
- `NXPY-204 <https://jira.nuxeo.com/browse/NXPY-204>`__: Fix data leak issue with mutable model properties
- `NXPY-205 <https://jira.nuxeo.com/browse/NXPY-205>`__: Improve S3 non-chunked uploads

Technical changes
-----------------

- Removed ``Batch.service`` class attribute
- Removed ``Blob.service`` class attribute
- Removed ``BufferBlob.stringio`` class attribute
- Removed ``Comment.service`` class attribute
- Removed ``FileBlob.fd`` class attribute
- Removed ``Directory.service`` class attribute
- Removed ``DirectoryEntry.service`` class attribute
- Removed ``Document.service`` class attribute
- Removed ``Group.service`` class attribute
- Removed ``Model.service`` class attribute
- Removed ``Model.uid`` class attribute
- Removed ``Operation.service`` class attribute
- Removed ``Task.service`` class attribute
- Removed ``User.service`` class attribute
- Removed ``Workflow.service`` class attribute

4.1.0
-----

Release date: ``2021-02-24``

- `NXPY-198 <https://jira.nuxeo.com/browse/NXPY-198>`__: Automatic deployment via GitHub Actions
- `NXPY-199 <https://jira.nuxeo.com/browse/NXPY-199>`__: Add support for idempotent calls
- `NXPY-202 <https://jira.nuxeo.com/browse/NXPY-202>`__: Add SSO with Portals authentication

Technical changes
-----------------

- Added ``TokenAuth.HEADER_TOKEN``
- Added nuxeo/auth/portal_sso.py
- Added nuxeo/auth/token.py
- Added nuxeo/auth/utils.py
- Removed nuxeo/auth.py
- Added nuxeo/constants.py::\ ``IDEMPOTENCY_KEY``
- Added nuxeo/exceptions.py::\ ``Conflict``
- Added nuxeo/exceptions.py::\ ``OngoingRequestError``

4.0.0
-----

Release date: ``2020-12-05``

- `NXPY-186 <https://jira.nuxeo.com/browse/NXPY-186>`__: Remove the ``Blob.batch_id`` attribute
- `NXPY-188 <https://jira.nuxeo.com/browse/NXPY-188>`__: Add mimetype tests
- `NXPY-191 <https://jira.nuxeo.com/browse/NXPY-191>`__: Fix ``urllib3`` DeprecationWarning in ``client.py``
- `NXPY-192 <https://jira.nuxeo.com/browse/NXPY-192>`__: Add support for Python 3.10
- `NXPY-193 <https://jira.nuxeo.com/browse/NXPY-193>`__: Fix thread-safety in uploads and workflows

Technical changes
-----------------

- Removed ``Blob.batch_id``. Use ``Blob.batchId`` instead.
- Removed utils.py::``SwapAttr``

3.1.1
-----

Release date: ``2020-11-12``

- `NXPY-188 <https://jira.nuxeo.com/browse/NXPY-188>`__: Set the ``Content-Type`` for uploads done via S3

3.1.0
-----

Release date: ``2020-11-06``

- `NXPY-183 <https://jira.nuxeo.com/browse/NXPY-183>`__: Set the TCP keep alive option by default
- `NXPY-184 <https://jira.nuxeo.com/browse/NXPY-184>`__: Fix ``test_upload_s3.py`` about ``IllegalLocationConstraintException``
- `NXPY-185 <https://jira.nuxeo.com/browse/NXPY-185>`__: Add the ``Blob.batchId`` attribute

Technical changes
-----------------

- Added ``Blob.batchId`` and deprecated ``Blob.batch_id``
- Added ``constants.LINUX``
- Added ``constants.MAC``
- Added ``constants.TCP_KEEPINTVL``
- Added ``constants.TCP_KEEPIDLE``
- Added ``constants.WINDOWS``
- Added nuxeo/tcp/tcp_keep_alive_probes.py

3.0.1
-----

Release date: ``2020-09-08``

- `NXPY-180 <https://jira.nuxeo.com/browse/NXPY-180>`__: Allow to upload to S3 when the bucket prefix is empty

3.0.0
-----

Release date: ``2020-08-25``

- `NXPY-159 <https://jira.nuxeo.com/browse/NXPY-159>`__: Allow to pass additional arguments to ``Batch.complete()``
- `NXPY-145 <https://jira.nuxeo.com/browse/NXPY-145>`__: Detect and log appropriate debug info when the transfer if chunked
- `NXPY-163 <https://jira.nuxeo.com/browse/NXPY-163>`__: Add the capability to refresh tokens in third-party batch handlers
- `NXPY-164 <https://jira.nuxeo.com/browse/NXPY-164>`__: Clean-up code smells found by Sourcery
- `NXPY-166 <https://jira.nuxeo.com/browse/NXPY-166>`__: Move to GitHub Actions for testing
- `NXPY-167 <https://jira.nuxeo.com/browse/NXPY-167>`__: Enable back Python 2.7 tests (+ fixes)
- `NXPY-168 <https://jira.nuxeo.com/browse/NXPY-168>`__: Rework Comments handling to work on all supported Nuxeo versions
- `NXPY-169 <https://jira.nuxeo.com/browse/NXPY-169>`__: Fix errors to fully re-support Nuxeo 9.10
- `NXPY-170 <https://jira.nuxeo.com/browse/NXPY-170>`__: Enforce ``NuxeoClient.server_info()`` robustness against invalid data
- `NXPY-171 <https://jira.nuxeo.com/browse/NXPY-171>`__: Set the timeout for uploads using the default handler
- `NXPY-172 <https://jira.nuxeo.com/browse/NXPY-172>`__: Always log the server response
- `NXPY-173 <https://jira.nuxeo.com/browse/NXPY-173>`__: Consign additionnal parameters sent to each HTTP requests in logs
- `NXPY-174 <https://jira.nuxeo.com/browse/NXPY-174>`__: Improve ``test_repository.py`` reliability
- `NXPY-176 <https://jira.nuxeo.com/browse/NXPY-176>`__: Add ``Nuxeo.can_use()`` to determine if a given operation is available
- `NXPY-177 <https://jira.nuxeo.com/browse/NXPY-177>`__: Prevent ``AttributeError`` when fetching the server version and the response is bad (and return "unknown")
- `NXPY-178 <https://jira.nuxeo.com/browse/NXPY-178>`__: Use a uniq ID for the S3 direct upload key
- `NXPY-179 <https://jira.nuxeo.com/browse/NXPY-179>`__: Use S3 accelerate endpoint when enabled

Technical changes
-----------------

- ``Batch.complete()`` now handles additional parameters
- Added ``Batch.key``
- Added ``Nuxeo.can_use()``
- Added ``Uploader.timeout()``
- Added nuxeo/constants.py::\ ``LOG_LIMIT_SIZE``
- nuxeo/uploads.py::\ ``API.complete()`` now handles additional parameters
- Added ``kwargs`` keyword arguments to nuxeo/uploads.py::\ ``API.send_data()``
- Added ``docuid`` argument to nuxeo/comments.py::\ ``API.get()``
- Added ``params`` keyword argument to nuxeo/comments.py::\ ``API.get()``
- Changed ``uid`` from positional argument to keyword argument in nuxeo/comments.py::\ ``API.get()``
- Added ``docuid`` argument to nuxeo/comments.py::\ ``API.post()``
- Changed ``comment (Comment)`` argument of nuxeo/comments.py::\ ``API.post()`` to ``text (str)``
- Added nuxeo/compat.py::\ ``lru_cache()``
- Changed nuxeo/constants.py::\ ``TIMEOUT_CONNECT`` from ``5`` to ``10``
- Changed nuxeo/constants.py::\ ``TIMEOUT_READ`` from ``30`` to ``600``
- Added nuxeo/uploads.py::\ ``API.refresh_token()``
- Added nuxeo/utils.py::\ ``cmp()``
- Added nuxeo/utils.py::\ ``get_response_content()``
- Added nuxeo/utils.py::\ ``version_compare()``
- Added nuxeo/utils.py::\ ``version_compare_client()``
- Added nuxeo/utils.py::\ ``version_le()``
- Added nuxeo/utils.py::\ ``version_lt()``

2.4.4
-----

Release date: ``2020-02-28``

- `NXPY-148 <https://jira.nuxeo.com/browse/NXPY-148>`__: Use the tmp_path fixture to auto-cleanup created files in tests
- `NXPY-155 <https://jira.nuxeo.com/browse/NXPY-155>`__: Don't use dots or underscores in custom HTTP headers
- `NXPY-156 <https://jira.nuxeo.com/browse/NXPY-156>`__: Do not silence S3 errors on upload resuming
- `NXPY-158 <https://jira.nuxeo.com/browse/NXPY-158>`__: Allow S3 custom endpoint for direct upload

2.4.3
-----

Release date: ``2020-01-31``

- `NXPY-151 <https://jira.nuxeo.com/browse/NXPY-151>`__: Do not log the full exception when retrieving MPU parts
- `NXPY-152 <https://jira.nuxeo.com/browse/NXPY-152>`__: Remove ``Uploader`` assert statements
- `NXPY-153 <https://jira.nuxeo.com/browse/NXPY-153>`__: Do not yield one more time only for S3 uploads
- `NXPY-154 <https://jira.nuxeo.com/browse/NXPY-154>`__: Fix S3 client instanciation not thread-safe

2.4.2
-----

Release date: ``2020-01-15``

- `NXPY-150 <https://jira.nuxeo.com/browse/NXPY-150>`__: Add ``nuxeo.uploads.has_s3()`` helper

Technical changes
-----------------

- Added ``nuxeo.uploads.has_s3()``

2.4.1
-----

Release date: ``2020-01-13``

- `NXPY-149 <https://jira.nuxeo.com/browse/NXPY-149>`__: Add ``Batch.is_s3()`` helper

Technical changes
-----------------

- Added ``Batch.is_s3()``

2.4.0
-----

Release date: ``2020-01-10``

- `NXPY-68 <https://jira.nuxeo.com/browse/NXPY-68>`__: Add the ``users.current_user()`` method
- `NXPY-138 <https://jira.nuxeo.com/browse/NXPY-138>`__: Add the Amazon S3 provider for uploads
- `NXPY-143 <https://jira.nuxeo.com/browse/NXPY-143>`__: Remove duplicate constructors code in ``models.py``

Technical changes
-----------------

- Added ``Batch.complete()``
- Added ``Batch.extraInfo``
- Added ``Batch.etag``
- Added ``Batch.multiPartUploadId``
- Added ``Batch.provider``
- Added nuxeo/constants.py::\ ``UP_AMAZON_S3``
- Added ``nuxeo.exceptions.InvalidUploadHandler``
- Added ``nuxeo/handlers/default.py``
- Added ``nuxeo/handlers/s3.py``
- Added ``nuxeo.uploads.complete()``
- Added ``nuxeo.uploads.handlers()``
- Added ``handler=""`` keyword argument to ``nuxeo.uploads.post()``
- Added ``data_len=0`` keyword argument to ``nuxeo.uploads.send_data()``
- Added ``nuxeo.users.current_user()``
- Added ``nuxeo.utils.chunk_partition()``
- Added ``nuxeo.utils.log_chunk_details()``
- Removed ``Batch.__init__()``
- Removed ``Comment.__init__()``
- Removed ``DirectoryEntry.__init__()``
- Removed ``Directory.__init__()``
- Removed ``Document.__init__()``
- Removed ``Group.__init__()``
- Removed ``Operation.__init__()``
- Removed ``Task.__init__()``
- Removed ``User.__init__()``
- Removed ``Workflow.__init__()``

2.3.0
-----

Release date: ``2019-12-06``

- `NXPY-131 <https://jira.nuxeo.com/browse/NXPY-131>`__: Make the HTTP response logging safer
- `NXPY-141 <https://jira.nuxeo.com/browse/NXPY-141>`__: Add the Comments API

Technical changes
-----------------

- Added nuxeo/comments.py
- Added `comments` argument to nuxeo/documents.py::\ ``API.__init__()``
- Added nuxeo/documents.py::\ ``API.comment_api`` attribute
- Added nuxeo/models.py::\ ``Comment`` class
- Added ``Document.comment()``
- Added ``Document.comments()``
- Added ``Nuxeo.comments``

2.2.4
-----

Release date: ``2019-10-29``

- `NXPY-128 <https://jira.nuxeo.com/browse/NXPY-128>`__: Make ``Batch`` upload index public
- `NXPY-135 <https://jira.nuxeo.com/browse/NXPY-135>`__: Expand the documentation on how to attach multiple blobs to a given document
- `NXPY-136 <https://jira.nuxeo.com/browse/NXPY-136>`__: Allow additionnal parameters to ``Directories.get()``
- `NXPY-137 <https://jira.nuxeo.com/browse/NXPY-137>`__: Fix failing test about converters
- `NXPY-139 <https://jira.nuxeo.com/browse/NXPY-139>`__: Enhance tox.ini to use multiple specific testenvs

Technical changes
-----------------

- nuxeo/directories.py::\ ``API.get()`` now handles additionnal parameters

2.2.3
-----

Release date: ``2019-09-30``

- `NXPY-125 <https://jira.nuxeo.com/browse/NXPY-125>`__: Add a warning for Python 2 removal
- `NXPY-130 <https://jira.nuxeo.com/browse/NXPY-130>`__: Expand the group examples to show subgroup handling
- `NXPY-132 <https://jira.nuxeo.com/browse/NXPY-132>`__: Add ``enrichers`` argument to ``Documents.get_children()``

2.2.2
-----

Release date: ``2019-08-26``

- `NXPY-112 <https://jira.nuxeo.com/browse/NXPY-112>`__: Update uploadedSize on each and every upload iteration
- `NXPY-110 <https://jira.nuxeo.com/browse/NXPY-110>`__: Max retries for all connections
- `NXPY-111 <https://jira.nuxeo.com/browse/NXPY-111>`__: Add timeouts handling
- `NXPY-113 <https://jira.nuxeo.com/browse/NXPY-113>`__: Use ``requests.sessions.Session`` rather than the deprecated ``requests.session``
- `NXPY-114 <https://jira.nuxeo.com/browse/NXPY-114>`__: Do not log the response of the CMIS endpoint
- `NXPY-117 <https://jira.nuxeo.com/browse/NXPY-117>`__: Use black for a one-shot big clean-up
- `NXPY-118 <https://jira.nuxeo.com/browse/NXPY-118>`__: Missing status code from ``Forbidden`` and ``Unauthorized`` exceptions
- `NXPY-119 <https://jira.nuxeo.com/browse/NXPY-119>`__: Remove the requests warning
- `NXPY-120 <https://jira.nuxeo.com/browse/NXPY-120>`__: Add a test for unavailable converters
- `NXPY-121 <https://jira.nuxeo.com/browse/NXPY-121>`__: Do not log the response of the automation endpoint
- `NXPY-123 <https://jira.nuxeo.com/browse/NXPY-123>`__: Pass the ``NXDRIVE_TEST_NUXEO_URL`` envar to tox
- `NXPY-126 <https://jira.nuxeo.com/browse/NXPY-126>`__: Allow several callables for transfer callbacks

Technical changes
-----------------

- Added ``NuxeoClient.disable_retry()``
- Added ``NuxeoClient.enable_retry()``
- Added ``NuxeoClient.retries``
- Added nuxeo/constants.py::\ ``MAX_RETRY``
- Added nuxeo/constants.py::\ ``RETRY_BACKOFF_FACTOR``
- Added nuxeo/constants.py::\ ``RETRY_METHODS``
- Added nuxeo/constants.py::\ ``RETRY_STATUS_CODES``
- Added nuxeo/constants.py::\ ``TIMEOUT_CONNECT``
- Added nuxeo/constants.py::\ ``TIMEOUT_READ``
- Changed nuxeo/exceptions.py::\ ``HTTPError`` to inherits from ``requests.exceptions.RetryError`` and ``NuxeoError``

2.2.1
-----

Release date: ``2019-06-27``

- `NXPY-108 <https://jira.nuxeo.com/browse/NXPY-108>`__: [Python 2] Fix ``repr(HTTPError)`` with non-ascii characters in the message

2.2.0
-----

Release date: unreleased

- `NXPY-102 <https://jira.nuxeo.com/browse/NXPY-102>`__: Set Upload operations to void operations
- `NXPY-103 <https://jira.nuxeo.com/browse/NXPY-103>`__: Launch flake8 on actual client data
- `NXPY-104 <https://jira.nuxeo.com/browse/NXPY-104>`__: Do not log server response based on content length but content type
- `NXPY-105 <https://jira.nuxeo.com/browse/NXPY-105>`__: Make a diffrence between HTTP 401 and 403 errors
- `NXPY-106 <https://jira.nuxeo.com/browse/NXPY-106>`__: Lower logging level in ``get_digester()``

Technical changes
-----------------

- Added nuxeo/client.py::\ ``HTTP_ERROR``
- Added nuxeo/exceptions.py::\ ``Forbidden``
- Added ``void_op=True`` keyword argument to nuxeo/uploads.py::\ ``API.execute()``

2.1.1
-----

Release date: ``2019-06-13``

- `NXPY-97 <https://jira.nuxeo.com/browse/NXPY-97>`__: Remove usage of pytest_namespace to allow using pytest > 4
- `NXPY-100 <https://jira.nuxeo.com/browse/NXPY-100>`__: Improve memory consumption

2.1.0
-----

Release date: ``2019-06-06``

- `NXPY-88 <https://jira.nuxeo.com/browse/NXPY-88>`__: Pass the file descriptor to Requests when doing a simple upload
- `NXPY-89 <https://jira.nuxeo.com/browse/NXPY-89>`__: Add ``repr(Uploader)`` to ease debug
- `NXPY-90 <https://jira.nuxeo.com/browse/NXPY-90>`__: Do not open file descriptor on empty file
- `NXPY-91 <https://jira.nuxeo.com/browse/NXPY-91>`__: Make uploads rely on server info for missing chunks
- `NXPY-92 <https://jira.nuxeo.com/browse/NXPY-92>`__: Fix ``server_info()`` default value check
- `NXPY-94 <https://jira.nuxeo.com/browse/NXPY-94>`__: Force write of file to disk
- `NXPY-95 <https://jira.nuxeo.com/browse/NXPY-95>`__: Use Sentry in tests
- `NXPY-96 <https://jira.nuxeo.com/browse/NXPY-96>`__: Fix tests execution not failing when it should do (+ clean-up)

Technical changes
-----------------

- Added ``Uploader.is_complete()``
- Added ``Uploader.process()``
- Removed ``chunked`` argument from ``Uploader.__init__()``
- Removed ``Uploader.index``
- Removed ``Uploader.init()``
- Removed ``Uploader.response``
- Renamed nuxeo/operations.py::\ ``API.save_to_file()`` ``check_suspended`` keyword argument to ``callback``
- Added nuxeo/uploads.py::\ ``ChunkUploader``
- Changed nuxeo/uploads.py::\ ``API.state()`` return value ``index`` (int) to ``uploaded_chunks`` (set)

2.0.5
-----

Release date: ``2019-03-28``

- `NXPY-80 <https://jira.nuxeo.com/browse/NXPY-80>`__: Stick with pytest < 4 to prevent internal error due to the use of deprecated ``pytest_namespace``
- `NXPY-81 <https://jira.nuxeo.com/browse/NXPY-81>`__: Fix flake8 errors and add flake8 to the CI
- `NXPY-82 <https://jira.nuxeo.com/browse/NXPY-82>`__: Fix ``test_convert_xpath()``
- `NXPY-83 <https://jira.nuxeo.com/browse/NXPY-83>`__: Fix ``test_convert()`` and ``test_convert_given_converter()``
- `NXPY-84 <https://jira.nuxeo.com/browse/NXPY-84>`__: Handle ``list`` type in operation parameters
- `NXPY-86 <https://jira.nuxeo.com/browse/NXPY-86>`__: Fix directories API
- `NXPY-87 <https://jira.nuxeo.com/browse/NXPY-87>`__: Add an upload helper to control the chunk uploads

Technical changes
-----------------

- Added ``Batch.get_uploader()``
- Added nuxeo/uploads.py::\ ``API.get_uploader()``
- Added `chunk_size` keyword argument to nuxeo/uploads.py::\ ``API.upload()``
- Added `chunk_size` keyword argument to nuxeo/uploads.py::\ ``API.state()``
- Removed `chunk_limit` keyword argument from nuxeo/uploads.py::\ ``API.upload()``
- Added ``callback`` keyword argument to nuxeo/uploads.py::\ ``API.upload()``
- Added nuxeo/uploads.py::\ ``Uploader``
- Added ``UploadError.info``

2.0.4
-----

Release date: ``2018-10-24``

- `NXPY-71 <https://jira.nuxeo.com/browse/NXPY-71>`__: Use tox to test the client on Python 2 and 3
- `NXPY-72 <https://jira.nuxeo.com/browse/NXPY-72>`__: Rely only on ``application/json`` content type
- `NXPY-74 <https://jira.nuxeo.com/browse/NXPY-74>`__: Add ``context`` as a property of Operation class


2.0.3
-----

Release date: ``2018-09-04``

- `NXPY-69 <https://jira.nuxeo.com/browse/NXPY-69>`__: Split the ``get_digester()`` function in two

Technical changes
-----------------

- Added utils.py::\ ``get_digest_algorithm()``
- Added utils.py::\ ``get_digest_hash()``

2.0.2
-----

Release date: ``2018-06-28``

- `NXPY-64 <https://jira.nuxeo.com/browse/NXPY-64>`__: Distribute a wheel on PyPi
- `NXPY-65 <https://jira.nuxeo.com/browse/NXPY-65>`__: Fix bytes <> str warnings
- `NXPY-67 <https://jira.nuxeo.com/browse/NXPY-67>`__: Fix Python 3.7 DeprecationWarning with ABCs

Technical changes
-----------------

- Removed compat.py::\ ``get_error_message()``

2.0.1
-----

Release date: ``2018-05-31``

- `NXPY-58 <https://jira.nuxeo.com/browse/NXPY-58>`__: Modify the client to fit in Nuxeo Drive
- `NXPY-63 <https://jira.nuxeo.com/browse/NXPY-63>`__: Handle multiblob uploads to a single document

Technical changes
~~~~~~~~~~~~~~~~~

- Added ``Batch.attach()``
- Added ``Batch.execute()``
- Added nuxeo/uploads.py::\ ``attach()``
- Added nuxeo/uploads.py::\ ``execute()``

2.0.0
-----

Release date: ``2018-05-18``

This is a refactoring of the module that **breaks** the compatibility with older versions.

- `NXPY-11 <https://jira.nuxeo.com/browse/NXPY-11>`__: Add usage examples
- `NXPY-16 <https://jira.nuxeo.com/browse/NXPY-16>`__: Move from urllib2 and poster to Requests
- `NXPY-26 <https://jira.nuxeo.com/browse/NXPY-26>`__: Use of setup.cfg
- `NXPY-37 <https://jira.nuxeo.com/browse/NXPY-37>`__: Add type checking for operation parameters
- `NXPY-40 <https://jira.nuxeo.com/browse/NXPY-40>`__: Add chunked resumable upload
- `NXPY-42 <https://jira.nuxeo.com/browse/NXPY-42>`__: Client refactoring
- `NXPY-54 <https://jira.nuxeo.com/browse/NXPY-54>`__: Add new Trash API
- A lot of code clean-up and improvement

Technical changes
~~~~~~~~~~~~~~~~~

- Added nuxeo/operations.py::\ ``API``
- Added nuxeo/tasks.py::\ ``API``
- Added ``APIEndpoint.exists()``
- Changed ``BatchBlob`` to ``Blob``
- Changed ``BatchUpload`` to nuxeo/uploads.py::\ ``API``
- Changed ``Blob._batchid`` to ``Blob.batchid``
- Changed ``Blob._service`` to ``Blob.service``
- Changed ``Directory`` to nuxeo/directories.py::\ ``API``
- Added ``Document.is_locked()``
- Added ``Document.isTrashed``
- Added ``Document.trash()``
- Added ``Document.untrash()``
- Removed ``FileBlob.get_upload_buffer()``
- Removed ``FileBlob._read_data()``
- Added nuxeo/compat.py::\ ``get_bytes()``
- Added nuxeo/compat.py::\ ``get_error_message()``
- Added nuxeo/compat.py::\ ``get_text()``
- Changed ``Groups`` to nuxeo/groups.py::\ ``API``
- Changed ``Nuxeo.request()`` to ``NuxeoClient.request()``
- Moved ``Nuxeo.InvalidBatchException`` to nuxeo/exceptions.py::\ ``InvalidBatch``
- Moved ``Nuxeo.Unauthorized`` to nuxeo/exceptions.py::\ ``Unauthorized``
- Removed ``Nuxeo.debug()``
- Removed ``Nuxeo.error()``
- Removed ``Nuxeo.force_decode()``
- Removed ``Nuxeo.trace()``
- Changed ``Nuxeo._check_params()`` to nuxeo/operations.py::\ ``API.check_params()``
- Removed ``Nuxeo._create_action()``
- Removed ``Nuxeo._end_action()``
- Removed ``Nuxeo._get_action()``
- Removed ``Nuxeo._get_common_headers()``
- Removed ``Nuxeo._get_cookies()``
- Changed ``Nuxeo._rest_url`` to ``NuxeoClient.api_path``
- Added nuxeo/client.py::\ ``NuxeoClient``
- Added ``NuxeoClient.server_info(force=False)``
- Added ``NuxeoClient.server_version``
- Changed ``NuxeoObject`` to ``Model``
- Changed ``NuxeoService`` to ``APIEndpoint``
- Changed ``Repository`` to nuxeo/documents.py::\ ``API``
- Added nuxeo/auth.py::\ ``TokenAuth``
- Added nuxeo/exceptions.py::\ ``UnavailableConvertor``
- Changed ``Users`` to nuxeo/users.py::\ ``API``
- Removed ``Workflows._map()``
- Changed ``Workflows`` to nuxeo/workflows.py::\ ``API``
