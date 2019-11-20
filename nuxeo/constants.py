# coding: utf-8
from __future__ import unicode_literals

# Force parameters verification for all operations
CHECK_PARAMS = False

# Chunk size to download files
CHUNK_SIZE = 8192  # 8 KiB

# API paths
DEFAULT_API_PATH = "api/v1"
DEFAULT_URL = "http://localhost:8080/nuxeo/"

# Default value for the:
#   - 'X-Application-Name' HTTP header
#   - 'applicationName' URL parameter
DEFAULT_APP_NAME = "Python client"

# Retries for each HTTP call on conection error
MAX_RETRY = 5

# Backoff factor between each retry
# Ex: with 0.2 then sleep() will sleep for [0.2s, 0.4s, 0.8s, ...] between retries
# Ex: with 1 then sleep() will sleep for [1s, 2s, 4s, ...] between retries
RETRY_BACKOFF_FACTOR = 1

# HTTP methods we want to handle in retries
RETRY_METHODS = frozenset(["GET", "POST", "PUT", "DELETE"])

# HTTP status code to handle for retries
RETRY_STATUS_CODES = [429, 500, 503, 504]

# Connection and read timeout, in seconds
TIMEOUT_CONNECT = 5
TIMEOUT_READ = 30

# Size of chunks for the upload
UPLOAD_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MiB

# Upload providers
UP_AMAZON_S3 = "s3"
