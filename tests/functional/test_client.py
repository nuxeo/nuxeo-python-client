from nuxeo.client import NuxeoClient


def test_client_is_reachable_without_verify():
    client = NuxeoClient()
    assert client.is_reachable()


def test_client_is_reachable_with_verify():
    client = NuxeoClient(verify=True)
    assert client.is_reachable()
    client = NuxeoClient(verify=False)
    assert client.is_reachable()


def test_request_with_kwargs_verify(server):
    assert server.client.request("GET", "json/cmis", verify=False)
    assert server.client.request("GET", "json/cmis", verify=True)


def test_request_with_ssl_verify(server):
    assert server.client.request("GET", "runningstatus", ssl_verify=False)
    assert server.client.request("GET", "runningstatus", ssl_verify=True)
