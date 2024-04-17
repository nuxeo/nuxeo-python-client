def test_request(server):

    import requests
    from unittest.mock import patch, Mock
    from ..constants import NUXEO_SERVER_URL

    flag = True

    def _request_no_aws(*args, **kwargs):
        nonlocal flag
        resp = Mock()
        resp.status_code = 302
        resp.headers = {"Location": f"{NUXEO_SERVER_URL}/api/v1/drive/configuration"}
        if flag:
            flag = False
            return resp
        resp = Mock()
        resp.status_code = 200
        flag = True
        return resp

    def _request_aws(*args, **kwargs):
        nonlocal flag
        resp = Mock()
        resp.status_code = 302
        resp.headers = {"Location": "amazonaws.com"}
        if flag:
            flag = False
            return resp
        resp = Mock()
        resp.status_code = 200
        flag = True
        return resp

    with patch.object(requests.sessions.Session, "request", new=_request_no_aws):
        resp = server.client.request("GET", "json/cmis")
        assert resp.status_code == 200

    with patch.object(requests.sessions.Session, "request", new=_request_aws):
        resp = server.client.request("GET", "json/cmis")
        assert resp.status_code == 200
