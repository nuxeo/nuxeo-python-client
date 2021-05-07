# coding: utf-8
"""

Most of this file's code has been taken from
https://github.com/requests/requests/blob/d58753344638992a63f4fe8e516c9f55a9a7f027/tests/testserver/server.py
and modified to fit our needs such as:
- Parsing a subset of upload queries
- Keeping track of uploaded chunks
- Options to generate 500 errors

"""
import json
import select
import socket
import threading
import uuid

from nuxeo.utils import get_bytes, get_text

uploads = {}


def consume_socket(sock, timeout=0.5):
    chunks = 65536
    content = b""

    while True:
        more_to_read = select.select([sock], [], [], timeout)[0]
        if not more_to_read:
            break

        new_content = sock.recv(chunks)
        if not new_content:
            break

        content += new_content

    return content


def generate_response(status, content=None):
    if content:
        content = json.dumps(content)
        length = len(content)
    else:
        length = 0
    response = "HTTP/1.1 {}\r\nContent-Length: {}\r\n\r\n{}"
    return get_bytes(response.format(status, length, content))


def parse_nuxeo_request(request_content):
    lines = request_content.split(b"\r\n")
    method, path, _ = get_text(lines.pop(0)).split(" ")
    path = path.split("/")[4:]
    headers = {}
    for line in lines:
        if not line:
            break
        h = get_text(line).split(": ")
        headers[h[0]] = h[1]
    return method, path, headers


def handle_nuxeo_request(request_content):
    method, path, headers = parse_nuxeo_request(request_content)
    try:
        if len(path) == 1 and path[0] == "upload" and method == "POST":
            # Create batch
            batch_id = str(uuid.uuid4())
            uploads[batch_id] = {}
            return generate_response("201 Created", {"batchId": batch_id})
        if len(path) == 3 and path[0] == "upload":
            batch_id, file_idx = path[1:]
            if method == "GET":
                # Get blob completeness
                blob = uploads[batch_id][file_idx]

                if len(blob["uploadedChunkIds"]) < int(blob["chunkCount"]):
                    return generate_response("308 Resume Incomplete", blob)
                else:
                    return generate_response("200 OK", blob)
            if method == "POST":
                # Upload blob
                upload_type = headers.get("X-Upload-Type", "normal")
                if upload_type == "normal":
                    blob = {
                        "name": headers["X-File-Name"],
                        "size": headers["Content-Length"],
                        "uploadType": upload_type,
                    }
                    uploads[batch_id][file_idx] = blob
                    return generate_response("200 OK", blob)

                blob = uploads.get(batch_id, {}).get(file_idx, None)
                if not blob:
                    blob = {
                        "batchId": batch_id,
                        "fileIdx": file_idx,
                        "uploadType": upload_type,
                        "uploadedChunkIds": [],
                        "uploadedSize": headers["Content-Length"],
                        "chunkCount": headers["X-Upload-Chunk-Count"],
                    }
                chunk_idx = headers["X-Upload-Chunk-Index"]
                if chunk_idx not in blob["uploadedChunkIds"]:
                    blob["uploadedChunkIds"].append(chunk_idx)
                uploads[batch_id][file_idx] = blob

                if len(blob["uploadedChunkIds"]) < int(blob["chunkCount"]):
                    return generate_response("308 Resume Incomplete", blob)
                else:
                    return generate_response("201 Created", blob)
    except Exception:
        return generate_response("404 Not Found")


class Server(threading.Thread):
    """Dummy server used for unit testing"""

    WAIT_EVENT_TIMEOUT = 5

    def __init__(
        self,
        handler=None,
        host="localhost",
        port=0,
        requests_to_handle=1,
        wait_to_close_event=None,
        **kwargs
    ):
        super().__init__()

        self.handler = handler or consume_socket
        self.handler_results = []
        self.fail_args = kwargs.get("fail_args", None)
        self.request_number = 0

        self.host = host
        self.port = port
        self.requests_to_handle = requests_to_handle

        self.wait_to_close_event = wait_to_close_event
        self.ready_event = threading.Event()
        self.stop_event = threading.Event()

    @classmethod
    def text_response_server(cls, text, request_timeout=0.5, **kwargs):
        def text_response_handler(sock):
            request_content = consume_socket(sock, timeout=request_timeout)
            sock.send(text.encode("utf-8"))

            return request_content

        return Server(text_response_handler, **kwargs)

    @classmethod
    def upload_response_server(cls, request_timeout=0.5, **kwargs):
        def upload_response_handler(sock):
            request_content = consume_socket(sock, timeout=request_timeout)
            resp = handle_nuxeo_request(request_content)
            sock.send(resp)
            sock.close()
            return request_content

        return Server(upload_response_handler, **kwargs)

    @classmethod
    def basic_response_server(cls, **kwargs):
        return cls.text_response_server(
            "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n", **kwargs
        )

    def run(self):
        try:
            self.server_sock = self._create_socket_and_bind()
            # in case self.port = 0
            self.port = self.server_sock.getsockname()[1]
            self.ready_event.set()
            self._handle_requests()

            if self.wait_to_close_event:
                self.wait_to_close_event.wait(self.WAIT_EVENT_TIMEOUT)
        finally:
            self.ready_event.set()  # just in case of exception
            self._close_server_sock_ignore_errors()
            self.stop_event.set()

    def _create_socket_and_bind(self):
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(0)
        return sock

    def _close_server_sock_ignore_errors(self):
        try:
            self.server_sock.close()
        except IOError:
            pass

    def _handle_requests(self):
        for _ in range(self.requests_to_handle):
            sock = self._accept_connection()
            if not sock:
                break

            fail_at = self.fail_args.get("fail_at", 0)
            fail_number = self.fail_args.get("fail_number", 0)
            if fail_at <= self.request_number < fail_at + fail_number:
                consume_socket(sock)
                sock.send(generate_response("500 Server Error"))
                sock.close()
                handler_result = ""
            else:
                handler_result = self.handler(sock)

            self.request_number += 1
            self.handler_results.append(handler_result)

    def _accept_connection(self):
        try:
            ready, _, _ = select.select(
                [self.server_sock], [], [], self.WAIT_EVENT_TIMEOUT
            )
            if not ready:
                return None

            return self.server_sock.accept()[0]
        except (select.error, socket.error, ValueError):
            # ValueError: file descriptor cannot be a negative integer (-1)
            return None

    def __enter__(self):
        self.start()
        self.ready_event.wait(self.WAIT_EVENT_TIMEOUT)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.stop_event.wait(self.WAIT_EVENT_TIMEOUT)
        else:
            if self.wait_to_close_event:
                # avoid server from waiting for event timeouts
                # if an exception is found in the main thread
                self.wait_to_close_event.set()

        # ensure server thread doesn't get stuck waiting for connections
        self._close_server_sock_ignore_errors()
        self.join()
        return False  # allow exceptions to propagate
