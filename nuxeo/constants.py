# coding: utf-8
from __future__ import unicode_literals

CHUNK_SIZE = 8192  # 8 Kio - Chunk size to download files
UPLOAD_CHUNK_SIZE = 256 * 1024  # 256 Kio - Size of chunks for the upload
CHUNK_LIMIT = 10 * 1024 * 1024  # 10 Mio - Maximum file size before enforcing chunk upload
MAX_RETRY = 3  # Retries for each upload/chunk upload before abandoning

DEFAULT_URL = 'http://localhost:8080/nuxeo/'
DEFAULT_API_PATH = 'api/v1'
DEFAULT_APP_NAME = 'Python client'
