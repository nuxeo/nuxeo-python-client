dev
---

Release date: ``2017-??-??``

-  `NXPY-11 <https://jira.nuxeo.com/browse/NXPY-11>`__: Add usage examples
-  `NXPY-14 <https://jira.nuxeo.com/browse/NXPY-14>`__: Quote Repository URLs
-  `NXPY-19 <https://jira.nuxeo.com/browse/NXPY-19>`__: Remove proxy support
-  `NXPY-22 <https://jira.nuxeo.com/browse/NXPY-22>`__: Sanitize relative URLs
-  `NXPY-25 <https://jira.nuxeo.com/browse/NXPY-25>`__: Allow strings as properties
-  `NXPY-26 <https://jira.nuxeo.com/browse/NXPY-26>`__: Use of setup.cfg
-  `NXPY-29 <https://jira.nuxeo.com/browse/NXPY-29>`__: Fix an encoding error in ``Nuxeo._log_details()``
-  `NXPY-37 <https://jira.nuxeo.com/browse/NXPY-37>`__: Add type checking for operation parameters
-  A lot of code clean-up and improvement

Technical changes
~~~~~~~~~~~~~~~~~

-  Changed ``BatchBlob._batchid`` to ``BatchBlob.batchid``
-  Changed ``BatchBlob._service`` to ``BatchBlob.service``
-  Changed ``Directory.fetchAll()`` to ``Directory.fetch_all()``
-  Added ``Document.is_locked()``
-  Moved ``FileBlob.get_upload_buffer()`` to
   nuxeo/blob.py::\ ``get_upload_buffer()``
-  Moved ``FileBlob._read_data()`` to nuxeo/blob.py::\ ``_read_data()``
-  Added ``Nuxeo.drive_config()``
-  Changed ``Nuxeo._check_params()`` to ``Nuxeo.check_params()``
-  Changed ``Nuxeo._rest_url`` to ``Nuxeo.rest_url``
-  Changed ``NuxeoObject._service`` to ``NuxeoObject.service``
-  Added ``NuxeoService.exists()``
-  Changed ``Operation._service`` to ``Operation.service``
-  Added ``Repository.exists()``
-  Changed ``Workflows._map()`` to ``Workflows.map()``
