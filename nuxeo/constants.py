# coding: utf-8
from __future__ import unicode_literals

# Force parameters verification for all operations
CHECK_PARAMS = False

# Maximum file size before enforcing chunk upload
CHUNK_LIMIT = 10 * 1024 * 1024  # 10 Mio

# Chunk size to download files
CHUNK_SIZE = 8192  # 8 Kio

# API paths
DEFAULT_API_PATH = 'api/v1'
DEFAULT_URL = 'http://localhost:8080/nuxeo/'

"""
Default value for the:
    - 'X-Application-Name' HTTP header
    - 'applicationName' URL parameter
"""
DEFAULT_APP_NAME = 'Python client'

# Retries for each upload/chunk upload before abandoning
MAX_RETRY = 3

# Size of chunks for the upload
UPLOAD_CHUNK_SIZE = 256 * 1024  # 256 Kio
