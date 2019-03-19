# coding: utf-8
from __future__ import unicode_literals

from .compat import get_bytes, quote, text
from .constants import CHUNK_LIMIT, MAX_RETRY, UPLOAD_CHUNK_SIZE
from .endpoint import APIEndpoint
from .exceptions import UploadError
from .models import Batch, Blob
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, Callable, List, Generator, Optional, Text, Tuple, Union  # noqa
        from .client import NuxeoClient  # noqa
        OptInt = Optional[int]  # noqa
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
            chunk_count = (blob.size // chunk_size
                           + (blob.size % chunk_size > 0))
            index = 0

        return chunk_size, chunk_count, index, info

    def upload(self, batch, blob, chunked=False, limit=CHUNK_LIMIT, callback=None):
        # type: (Batch, Blob, bool, int, Callable) -> Blob
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
        chunked = chunked or blob.size > limit
        uploader = Uploader(self, batch, blob, chunked, callback)
        uploader.upload()
        return uploader.response

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

    def get_uploader(self, batch, blob, chunked=False, limit=CHUNK_LIMIT, callback=None):
        # type: (Batch, Blob, bool, int, Callable) -> Uploader
        """
        Get an upload helper for blob.

        Can be used to upload a new blob or resume
        the upload of a chunked blob.

        :param batch: batch of the upload
        :param blob: blob to upload
        :param chunked: if True, send in chunks
        :param limit: if blob is bigger, send in chunks
        :return: uploaded blob details
        """

        chunked = chunked or blob.size > limit
        return Uploader(self, batch, blob, chunked, callback)


class Uploader:
    """ Helper for uploads """
    def __init__(self, service, batch, blob, chunked, callback=None):
        # type: (API, Batch, Blob, bool, Callable) -> None
        self.service = service
        self.batch = batch
        self.blob = blob
        self.chunked = chunked
        self.callback = callback
        self.headers = service.headers.copy()
        self.response = None

        self.init()

    def init(self):
        # type: () -> None
        """ Compute the headers, the path, the chunking info, etc. """
        self.chunked = self.chunked and self.blob.size > 0

        self.headers.update({
            'Cache-Control': 'no-cache',
            'X-File-Name': quote(get_bytes(self.blob.name)),
            'X-File-Size': text(self.blob.size),
            'X-File-Type': self.blob.mimetype,
            'Content-Length': text(self.blob.size),
        })

        self.path = '{}/{}'.format(self.batch.batchId, self.batch._upload_idx)

        if self.chunked:
            chunk_size, chunk_count, index, info = self.service.state(self.path, self.blob)

            self.headers.update({
                'X-Upload-Type': 'chunked',
                'X-Upload-Chunk-Count': text(chunk_count),
                'Content-Length': text(chunk_size)
            })
        else:
            chunk_size, chunk_count, index = self.blob.size or None, 1, 0

        self.chunk_size = chunk_size
        self.chunk_count = chunk_count
        self.index = index

    def upload(self, generate=False):
        # type: (Optional[bool]) -> Optional[Generator]
        """
        Upload the file.

        If the `Uploader` has a callback, it is run after each chunk upload.

        If `generate` is True, the method will yield after the callback step.
        To complete the entire file upload, the generator should be consumed
        in a `for .. in ..` loop or until it raises `StopIteration`.
        The generator yields the uploader itself since it contains all relevant data.

        """

        if self.index == self.chunk_count:
            # All the parts have been uploaded, update the attributes
            self.response.batch_id = self.batch.uid
            self.batch.blobs[self.batch._upload_idx] = self.response
            self.batch._upload_idx += 1

        with self.blob as src:
            # Seek to the right position if the upload is starting
            src.seek(self.index * self.chunk_size)

            while self.index < self.chunk_count:
                # Read a chunk of data
                data = src.read(self.chunk_size) if self.chunk_size else src.read()
                # Upload it
                self.response = self.service.send_data(
                    self.blob.name, data, self.path, self.chunked, self.index, self.headers)
                # Keep track of the current index
                self.index += 1
                # Call the callback if it exists
                if callable(self.callback):
                    self.callback(self)
                # Yield to the upper scope if the "generate" mode is on
                if generate:
                    yield self
