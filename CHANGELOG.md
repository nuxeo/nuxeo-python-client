# dev
Release date: `2017-??-??`

- [NXPY-29](https://jira.nuxeo.com/browse/NXPY-29): Encoding error in _log_details
- [NXPY-30](https://jira.nuxeo.com/browse/NXPY-30): Add a method to fetch the server's configuration file
- [NXPY-31](https://jira.nuxeo.com/browse/NXPY-31): Improve methods organization in classes
- [NXPY-33](https://jira.nuxeo.com/browse/NXPY-33): Skip tests that requires office2html on macOS
- [NXPY-34](https://jira.nuxeo.com/browse/NXPY-34): Convert tests to pytest

### Technical changes
- Changed `BatchBlob._batchid` to `BatchBlob.batchid`
- Changed `BatchBlob._service` to `BatchBlob.service`
- Changed `Directory.fetchAll()` to `Directory.fetch_all()`
- Moved nuxeo/blob.py::`FileBlob.get_upload_buffer(input_file)` to nuxeo/blob.py::`get_upload_buffer(input_file)`
- Moved nuxeo/blob.py::`FileBlob._read_data(file_object, buffer_size)` to nuxeo/blob.py::`_read_data(file_object, buffer_size))`
- Added `Nuxeo.drive_config()`
- Changed `Nuxeo._rest_url` to `Nuxeo.rest_url`
- Changed `NuxeoObject._service` to `NuxeoObject.service`
- Added `NuxeoService.exists(uid)`
- Changed `Operation._service` to `Operation.service`
- Added `Repository.exists(path)`
- Changed `Workflows._map(result, cls)` to `Workflows.map(result, cls)`