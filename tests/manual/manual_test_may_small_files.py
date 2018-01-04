# coding: utf-8
from __future__ import unicode_literals

import os
import random

from memory_profiler import profile

from nuxeo.client import Nuxeo
from nuxeo.models import Document, FileBlob


@profile
def upload_random_file(server, file_in, i):
    filename = '{}_{}'.format(file_in, i)
    r_size = random.randint(10, 500)
    with open(filename, 'wb') as f:
        f.write(b'\x00' + os.urandom(r_size*100*1024) + b'\x00')

    batch = server.uploads.batch()
    batch.upload(FileBlob(filename, mimetype='application/octet-stream'))
    doc = server.documents.create(
        Document(
            name='Foo{}'.format(i),
            type='File',
            properties={
                'dc:title': 'foo{}'.format(i),
            }
        ), parent_path='/default-domain/workspaces')
    try:
        operation = server.operations.new('Blob.AttachOnDocument')
        operation.params = {'document': doc.path}
        operation.input_obj = batch.get(0)
        operation.execute(void_op=True)
    except:
        doc.delete()
    else:
        return doc


@profile
def download_file(server, file_in, file_out, i):
    filename = '{}_{}'.format(file_in, i)
    try:
        operation = server.operations.new('Blob.Get')
        operation.input_obj = '{}/Foo{}'.format(
            '/default-domain/workspaces', i)
        operation.execute(file_out=file_out)
    finally:
        os.remove(filename)
        os.remove(file_out)

@profile
def run_test(server):
    file_in, file_out = 'test_in', 'test_out'
    n = 10
    docs = []
    for i in range(n):
        docs.append(
            upload_random_file(
                server, file_in, i))

    for i in range(n):
        download_file(
            server, file_in, file_out, i)

    for doc in docs:
        doc.delete()


if __name__ == '__main__':
    server = Nuxeo(host=os.environ.get('NXDRIVE_TEST_NUXEO_URL',
                                       'http://localhost:8080/nuxeo'),
                   auth=('Administrator', 'Administrator'))
    server.client.set(schemas=['dublincore'])
    run_test(server)
