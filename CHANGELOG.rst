Changelog
=========

dev
---

Release date: ``2018-??-??``

-  `NXPY-11 <https://jira.nuxeo.com/browse/NXPY-11>`__: Add usage examples
-  `NXPY-14 <https://jira.nuxeo.com/browse/NXPY-14>`__: Quote Repository URLs
-  `NXPY-16 <https://jira.nuxeo.com/browse/NXPY-16>`__: Move from urllib2 and poster to Requests
-  `NXPY-19 <https://jira.nuxeo.com/browse/NXPY-19>`__: Remove proxy support
-  `NXPY-22 <https://jira.nuxeo.com/browse/NXPY-22>`__: Sanitize relative URLs
-  `NXPY-26 <https://jira.nuxeo.com/browse/NXPY-26>`__: Use of setup.cfg
-  `NXPY-37 <https://jira.nuxeo.com/browse/NXPY-37>`__: Add type checking for operation parameters
-  `NXPY-40 <https://jira.nuxeo.com/browse/NXPY-40>`__: Add chunked resumable upload
-  `NXPY-42 <https://jira.nuxeo.com/browse/NXPY-42>`__: Client refactoring
-  A lot of code clean-up and improvement

Technical changes
~~~~~~~~~~~~~~~~~

-  Added nuxeo/operations.py::\ ``API``
-  Added nuxeo/tasks.py::\ ``API``
-  Added ``APIEndpoint.exists()``
-  Changed ``BatchBlob`` to ``Blob``
-  Changed ``BatchUpload`` to nuxeo/uploads.py::\ ``API``
-  Changed ``Blob._batchid`` to ``Blob.batchid``
-  Changed ``Blob._service`` to ``Blob.service``
-  Changed ``Directory`` to nuxeo/directories.py::\ ``API``
-  Added ``Document.is_locked()``
-  Removed ``FileBlob.get_upload_buffer()``
-  Removed ``FileBlob._read_data()``
-  Added nuxeo/compat.py::\ ``get_bytes()``
-  Added nuxeo/compat.py::\ ``get_error_message()``
-  Added nuxeo/compat.py::\ ``get_text()``
-  Changed ``Groups`` to nuxeo/groups.py::\ ``API``
-  Changed ``Nuxeo.request()`` to ``NuxeoClient.request()``
-  Moved ``Nuxeo.InvalidBatchException`` to
   nuxeo/exceptions.py::\ ``InvalidBatch``
-  Moved ``Nuxeo.Unauthorized`` to nuxeo/exceptions.py::\ ``Unauthorized``
-  Removed ``Nuxeo.debug()``
-  Removed ``Nuxeo.error()``
-  Removed ``Nuxeo.force_decode()``
-  Removed ``Nuxeo.trace()``
-  Changed ``Nuxeo._check_params()`` to
   nuxeo/operations.py::\ ``API.check_params()``
-  Removed ``Nuxeo._create_action()``
-  Removed ``Nuxeo._end_action()``
-  Removed ``Nuxeo._get_action()``
-  Removed ``Nuxeo._get_common_headers()``
-  Removed ``Nuxeo._get_cookies()``
-  Changed ``Nuxeo._rest_url`` to ``NuxeoClient.api_path``
-  Added nuxeo/client.py::\ ``NuxeoClient``
-  Changed ``NuxeoObject`` to ``Model``
-  Changed ``NuxeoService`` to ``APIEndpoint``
-  Changed ``Repository`` to nuxeo/documents.py::\ ``API``
-  Added nuxeo/auth.py::\ ``TokenAuth``
-  Added nuxeo/exceptions.py::\ ``UnavailableConvertor``
-  Changed ``Users`` to nuxeo/users.py::\ ``API``
-  Removed ``Workflows._map()``
-  Changed ``Workflows`` to nuxeo/workflows.py::\ ``API``
