Changelog
=========

2.0.6
-----

Release date: ``2019-XX-XX``

- `NXPY-88 <https://jira.nuxeo.com/browse/NXPY-88>`__: Pass the file descriptor to Requests when doing a simple upload
- `NXPY-89 <https://jira.nuxeo.com/browse/NXPY-89>`__: Add ``repr(Uploader)`` to ease debug

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
