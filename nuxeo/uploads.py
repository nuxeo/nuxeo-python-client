# coding: utf-8
from __future__ import unicode_literals

from nuxeo.exceptions import UploadError
from .compat import quote, text, get_bytes
from .constants import CHUNK_LIMIT, MAX_RETRY, UPLOAD_CHUNK_SIZE
from .endpoint import APIEndpoint
from .models import Batch, Blob
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text, Tuple, Union
        from .client import NuxeoClient
        OptInt = Optional[int]
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for uploads. """
    def __init__(self, client, endpoint='upload', headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(
            client, endpoint=endpoint, cls=Blob, headers=headers)

    def get(self, batch_id, file_idx=None):
        # type: (Text, Optional[int]) -> Union[List[Blob], Blob]
        """
        Get the detail of a batch.

        If file_idx is None, returns the details of all its blobs,
        otherwise returns the details of the corresponding blob.

        :param batch_id: the id of the batch
        :param file_idx: the index of the blob
        :return: the batch details
        """
        path = batch_id
        if file_idx is not None:
            path = '{}/{}'.format(path, file_idx)

        resource = super(API, self).get(path=path)

        if file_idx is not None:
            resource.batch_id = batch_id
            resource.fileIdx = file_idx
        elif not resource:
            return []
        return resource

    def post(self):
        # type: () -> Batch
        """
        Create a batch.

        :return: the created batch
        """
        response = self.client.request('POST', self.endpoint)
        return Batch.parse(response.json(), service=self)

    batch = post  # Alias for clarity

    def put(self, **kwargs):
        # type: (Any) -> None
        raise NotImplementedError()

    def delete(self, batch_id, file_idx=None):
        # type: (Text, Optional[int]) -> None
        """
        Delete a batch or a blob.

        If the file_idx is None, deletes the batch,
        otherwise deletes the corresponding blob.

        :param batch_id: the id of the batch
        :param file_idx: the index of the blob
        """
        if file_idx is not None:
            target = '{}/{}'.format(batch_id, file_idx)
            super(API, self).delete(target)
        else:
            target = batch_id
            with SwapAttr(self, '_cls', Batch):
                super(API, self).delete(target)

    def send_data(
        self,
        name,  # type: Text
        data,  # type: Union[Text, bytes]
        path,  # type: Text
        chunked,  # type: bool
        index,  # type: int
        headers,  # type: Dict[Text, Text]
    ):
        # type: (...) -> Blob
        """
        Send data/chunks to the server.


        :param name: name of the file being uploaded
        :param data: data being sent
        :param path: url for the upload
        :param chunked: True if the upload is in chunks
        :param index: which chunk is being sent (0 if not chunked)
        :param headers: HTTP request headers
        :return: the blob info
        """
        if chunked:
            headers['X-Upload-Chunk-Index'] = text(index)

        for i in range(MAX_RETRY):
            response = super(API, self).post(
                resource=data,
                path=path,
                raw=True,
                headers=headers,
                default={}
            )
            if response:
                break
        else:
            chunk = index if chunked else None
            raise UploadError(name, chunk=chunk)
        return response

    def state(self, path, blob):
        # type: (Text, Blob) -> Tuple[OptInt, OptInt, OptInt, Blob]
        """
        Get the state of a blob.

        If the blob upload has not begun yet, the server
        will return a 404 error, so we initialize the
        different values.
        If the blob upload is incomplete, we return the
        values the server sent us.
        If the blob upload is complete, we return None
        for these values.

        :param path: path for the request
        :param blob: the target blob
        :return: the chunk size, chunk count, the index
                 of the next blob to upload, and the
                 response from the server
        """
        info = super(API, self).get(path, default=None)

        if info:
            chunk_count = int(info.chunkCount)
            chunk_size = int(info.uploadedSize)
            index = int(info.uploadedChunkIds[-1]) + 1
        else:  # It's a new upload
            chunk_size = UPLOAD_CHUNK_SIZE
            chunk_count = (blob.size // chunk_size +
                           (blob.size % chunk_size > 0))
            index = 0

        return chunk_size, chunk_count, index, info

    def upload(self, batch, blob, chunked=False, limit=CHUNK_LIMIT):
        # type: (Batch, Blob, bool, int) -> Blob
        """
        Upload a blob.

        Can be used to upload a new blob or resume
        the upload of a chunked blob.

        :param batch: batch of the upload
        :param blob: blob to upload
        :param chunked: if True, send in chunks
        :param limit: if blob is bigger, send in chunks
        :return: uploaded blob details
        """
        chunked = (chunked or blob.size > limit) and blob.size > 0
        response = None

        headers = self.headers
        headers.update({
            'Cache-Control': 'no-cache',
            'X-File-Name': quote(get_bytes(blob.name)),
            'X-File-Size': text(blob.size),
            'X-File-Type': blob.mimetype,
            'Content-Length': text(blob.size),
        })

        path = '{}/{}'.format(batch.batchId, batch._upload_idx)

        if chunked:
            chunk_size, chunk_count, index, info = self.state(path, blob)

            headers.update({
                'X-Upload-Type': 'chunked',
                'X-Upload-Chunk-Count': text(chunk_count),
                'Content-Length': text(chunk_size)
            })
        else:
            chunk_size, chunk_count, index = blob.size or None, 1, 0

        with blob as source:
            if index:
                source.seek(index * chunk_size)
            while index < chunk_count:
                data = source.read(chunk_size) if chunk_size else source.read()
                response = self.send_data(
                    blob.name, data, path, chunked, index, headers)
                index += 1

        response.batch_id = batch.uid
        return response

    def execute(self, batch, operation, file_idx=None, params=None):
        # type: (Batch, Text, Optional[int], Optional[Dict[Text,Any]]) -> Any
        """
        Execute an operation with the batch or one of its files as an input.

        :param batch: input for the operation
        :param operation: operation to execute
        :param file_idx: if not None, sole input of the operation
        :param params: parameters for the operation
        :return: the output of the operation
        """
        path = '{}/{}'.format(self.endpoint, batch.uid)
        if file_idx is not None:
            path = '{}/{}'.format(path, file_idx)

        path = '{}/execute/{}'.format(path, operation)

        return self.client.request('POST', path, data={'params': params})

    def attach(self, batch, doc, file_idx=None):
        # type: (Batch, Text, Optional[int]) -> Any
        """
        Attach one or all files of a batch to a document.

        :param batch: batch to attach
        :param doc: document to attach
        :param file_idx: if not None, only this file will be attached
        :return: the output of the attach operation
        """
        params = {'document': doc}
        if file_idx is None and batch._upload_idx > 1:
            params['xpath'] = 'files:files'
        return self.execute(batch, 'Blob.Attach', file_idx, params)
