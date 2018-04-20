# coding: utf-8
from __future__ import unicode_literals

# Chunk size to download files
CHUNK_SIZE = 8192  # 8 Kio

# Size of chunks for the upload
UPLOAD_CHUNK_SIZE = 256 * 1024  # 256 Kio

# Maximum file size before enforcing chunk upload
CHUNK_LIMIT = 10 * 1024 * 1024  # 10 Mio

# Retries for each upload/chunk upload before abandoning
MAX_RETRY = 3

# API paths
DEFAULT_URL = 'http://localhost:8080/nuxeo/'
DEFAULT_API_PATH = 'api/v1'

"""
Default value for the:
    - 'X-Application-Name' HTTP header
    - 'applicationName' URL parameter
"""
DEFAULT_APP_NAME = 'Python client'

# Force parameters verification for all operations
CHECK_PARAMS = False
