# coding: utf-8
import os
import random
from memory_profiler import profile

from nuxeo.client import Nuxeo
from nuxeo.models import Document, FileBlob
from tests.constants import NUXEO_SERVER_URL


def create_random_file(file_in, i):
    filename = f"{file_in}_{i}"
    r_size = random.randint(10, 500)
    with open(filename, "wb") as f:
        f.write(b"\x00" + os.urandom(r_size * 100 * 1024) + b"\x00")
    return filename


@profile
def upload_file(server, filename):
    batch = server.uploads.batch()
    batch.upload(FileBlob(filename))
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
    else:
        return doc


@profile
def download_file(server, file_in, i):
    filename = f"{file_in}_{i}"
    file_out = f"{filename}.dl"
    try:
        operation = server.operations.new("Blob.Get")
        operation.input_obj = f"/default-domain/workspaces/{filename}"
        operation.execute(file_out=file_out)
    finally:
        os.remove(filename)
        os.remove(file_out)


@profile
def run_test(server):
    file_in = "test_in"
    n = 10
    docs = []
    for i in range(n):
        filename = create_random_file(file_in, i)
        docs.append(upload_file(server, filename))

    for i in range(n):
        download_file(server, file_in, i)

    for doc in docs:
        doc.delete()


if __name__ == "__main__":
    server = Nuxeo(
        host=os.environ.get("NXDRIVE_TEST_NUXEO_URL", NUXEO_SERVER_URL),
        auth=("Administrator", "Administrator"),
    )
    server.client.set(schemas=["dublincore"])
    run_test(server)
