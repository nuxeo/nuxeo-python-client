from ..constants import NUXEO_SERVER_URL
from nuxeo.client import NuxeoClient


def test_request():
    client = NuxeoClient()
    assert client.is_reachable()
    client.ssl_verify_needed = None
    assert client.request("GET", "", verify=False)
