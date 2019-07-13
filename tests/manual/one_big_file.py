# coding: utf-8
from __future__ import unicode_literals

import os
from memory_profiler import profile

from nuxeo.client import Nuxeo
from nuxeo.models import Document, FileBlob


@profile
def create_file(filename):
    with open(filename, "wb") as f:
        f.write(b"0" * 1024 * 1024 * 1024)  # 1 Go


@profile
def upload_file(server, filename):
    batch = server.uploads.batch()
    batch.upload(FileBlob(filename, mimetype="application/octet-stream"))
    doc = server.documents.create(
        Document(name=filename, type="File", properties={"dc:title": filename}),
        parent_path="/default-domain/workspaces",
    )
    try:
        operation = server.operations.new("Blob.AttachOnDocument")
        operation.params = {"document": doc.path}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)
    except Exception:
        doc.delete()
    return doc


@profile
def download_file(server, filename):
    operation = server.operations.new("Blob.Get")
    operation.input_obj = "/default-domain/workspaces/{}".format(filename)
    operation.execute(file_out=filename)


@profile
def run_test(server):
    filename = "big_mama.bin"
    create_file(filename)

    doc = upload_file(server, filename)
    os.remove(filename)

    download_file(server, filename)
    doc.delete()


if __name__ == "__main__":
    server = Nuxeo(
        host=os.environ.get("NXDRIVE_TEST_NUXEO_URL", "http://localhost:8080/nuxeo"),
        auth=("Administrator", "Administrator"),
    )
    server.client.set(schemas=["dublincore"])
    run_test(server)
