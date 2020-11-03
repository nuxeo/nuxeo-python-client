# coding: utf-8
from __future__ import unicode_literals

from sys import platform

# OS
LINUX = platform.startswith("linux")
MAC = platform == "darwin"
WINDOWS = platform == "win32"

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

# Maximum size to not overflow when logging raw content of a HTTP response
LOG_LIMIT_SIZE = 5 * 1024 * 1024  # 5 MiB

# Retries for each HTTP call on conection error
MAX_RETRY = 5

# Backoff factor between each retry
# Ex: with 0.2 then sleep() will sleep for [0.2s, 0.4s, 0.8s, ...] between retries
# Ex: with 1 then sleep() will sleep for [1s, 2s, 4s, ...] between retries
RETRY_BACKOFF_FACTOR = 1

# HTTP methods we want to handle in retries
RETRY_METHODS = frozenset(["GET", "POST", "PUT", "DELETE"])

# HTTP status code to handle for retries
# 425 Too Early
# 500 Internal Server Error
# 503 Service Unavailable
# 504 Gateway Timeout
RETRY_STATUS_CODES = [429, 500, 503, 504]

# TCP Keep Alive
# The content to send on macOS in the TCP Keep Alive probes
TCP_KEEPALIVE = 0x10
# The interval between probes
TCP_KEEPALIVE_INTERVAL = 60
# The maximum number of failed probes before terminating the connection
TCP_KEEP_CNT = 3
# The maximum time to keep the connection idle before sending probes
TCP_KEEP_IDLE = 60

# Connection and read timeout, in seconds
TIMEOUT_CONNECT = 10
TIMEOUT_READ = 60 * 10

# Size of chunks for the upload
UPLOAD_CHUNK_SIZE = 20 * 1024 * 1024  # 20 MiB

# Upload providers
UP_AMAZON_S3 = "s3"
