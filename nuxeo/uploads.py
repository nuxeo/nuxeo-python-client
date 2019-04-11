# coding: utf-8
from __future__ import unicode_literals

from .compat import get_bytes, quote, text
from .constants import MAX_RETRY, UPLOAD_CHUNK_SIZE
from .endpoint import APIEndpoint
from .exceptions import HTTPError, UploadError
from .models import Batch, Blob
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, BinaryIO, Callable, Dict, List, Generator, Optional, Set, Text, Tuple, Union  # noqa
        from .client import NuxeoClient  # noqa
        from .models import BufferBlob, FileBlob  # noqa
        ActualBlob = Union[BufferBlob, FileBlob]  # noqa
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
        data,  # type: Union[BinaryIO, Text, bytes]
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

        server_error = None
        for _ in range(MAX_RETRY):
            try:
                response = super(API, self).post(
                    resource=data,
                    path=path,
                    raw=True,
                    headers=headers
                )
                if response:
                    break
            except HTTPError as e:
                server_error = e
        else:
            chunk = index if chunked else None
            raise UploadError(name, chunk=chunk, info=server_error)
        return response

    def state(self, path, blob, chunk_size=UPLOAD_CHUNK_SIZE):
        # type: (Text, ActualBlob, int) -> Tuple[OptInt, OptInt, Set, Blob]
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
        :param chunk_size: the chunk size for new uploads
        :return: the chunk size, chunk count, the index
                 of the next blob to upload, and the
                 response from the server
        """
        info = super(API, self).get(path, default=None)

        if info:
            chunk_count = int(info.chunkCount)
            uploaded_chunks = set(info.uploadedChunkIds)
        else:  # It's a new upload
            chunk_count = (blob.size // chunk_size
                           + (blob.size % chunk_size > 0))
            uploaded_chunks = set()

        return chunk_count, uploaded_chunks, info

    def upload(
        self,
        batch,  # type: Batch
        blob,  # type: ActualBlob
        chunked=False,  # type: bool
        chunk_size=UPLOAD_CHUNK_SIZE,  # type: int
        callback=None,  # type: Callable
    ):
        # type: (...) -> Blob
        """
        Upload a blob.

        Can be used to upload a new blob or resume
        the upload of a chunked blob.

        :param batch: batch of the upload
        :param blob: blob to upload
        :param chunked: if True, send in chunks
        :param chunk_size: if blob is bigger, send in chunks of this size
        :param callback: if not None, it is executed between each chunk
        :return: uploaded blob details
        """
        uploader = self.get_uploader(batch, blob, chunked, chunk_size, callback=callback)
        uploader.upload()
        return uploader.blob

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

    def get_uploader(
        self,
        batch,  # type: Batch
        blob,  # type: ActualBlob
        chunked=False,  # type: bool
        chunk_size=UPLOAD_CHUNK_SIZE,  # type: int
        callback=None,  # type: Callable
    ):
        # type: (...) -> Uploader
        """
        Get an upload helper for blob.

        Can be used to upload a new blob or resume
        the upload of a chunked blob.

        :param batch: batch of the upload
        :param blob: blob to upload
        :param chunked: if True, send in chunks
        :param chunk_size: if blob is bigger, send in chunks of this size
        :param callback: if not None, it is executed between each chunk
        :return: uploaded blob details
        """
        chunked = chunked and blob.size > chunk_size
        if chunked:
            return ChunkUploader(self, batch, blob, chunk_size, callback)
        return Uploader(self, batch, blob, chunk_size, callback)


class Uploader(object):
    """ Helper for uploads """
    chunked = False

    def __init__(self, service, batch, blob, chunk_size, callback=None):
        # type: (API, Batch, ActualBlob, int, Callable) -> None
        self.service = service
        self.batch = batch
        self.blob = blob
        self.chunk_size = chunk_size
        self.callback = callback
        self.headers = service.headers.copy()

        self.chunk_size = self.blob.size or None
        self.chunk_count = 1
        self.path = '{}/{}'.format(self.batch.batchId, self.batch._upload_idx)

        self.headers.update({
            'Cache-Control': 'no-cache',
            'X-File-Name': quote(get_bytes(self.blob.name)),
            'X-File-Size': text(self.blob.size),
            'X-File-Type': self.blob.mimetype,
            'Content-Length': text(self.blob.size),
        })

    def __repr__(self):
        # type: () -> Text
        return "<{} blob={!r}, chunked={!r}, chunk_size={!r}>".format(
            type(self).__name__,
            self.blob,
            self.chunked,
            self.chunk_size,
        )

    def __str__(self):
        # type: () -> Text
        return repr(self)

    def is_complete(self):
        # type: () -> bool
        return getattr(self, "_completed", False)

    def process(self, response):
        # type: (Blob) -> None
        self.blob.fileIdx = response.fileIdx

    def upload(self):
        # type: () -> None
        """ Upload the file. """
        with self.blob as src:
            data = src if self.blob.size else None
            self.process(self.service.send_data(
                self.blob.name, data, self.path, self.chunked, 0, self.headers
            ))
            if callable(self.callback):
                self.callback(self)
            setattr(self, "_completed", True)
        self._update_batch()

    def _update_batch(self):
        # type: () -> None
        """ Add the uploaded blob info to the batch. """
        if self.is_complete():
            # All the parts have been uploaded, update the attributes
            self.blob.batch_id = self.batch.uid
            self.batch.blobs[self.batch._upload_idx] = self.blob
            self.batch._upload_idx += 1


class ChunkUploader(Uploader):
    """ Helper for chunked uploads """
    chunked = True

    def __init__(self, service, batch, blob, chunk_size, callback=None):
        # type: (API, Batch, ActualBlob, int, Callable) -> None
        super(ChunkUploader, self).__init__(service, batch, blob, chunk_size, callback=callback)
        chunk_count, uploaded_chunks, info = self.service.state(
            self.path, self.blob, chunk_size
        )
        self.headers.update({
            'X-Upload-Type': 'chunked',
            'X-Upload-Chunk-Count': text(chunk_count),
            'Content-Length': text(chunk_size)
        })

        self.chunk_size = chunk_size
        self.chunk_count = chunk_count
        self.blob.uploadedChunkIds = uploaded_chunks
        self.blob.chunkCount = chunk_count
        self._to_upload = set()
        self._compute_chunks_left()

    def _compute_chunks_left(self):
        # type: () -> None
        """ Compare the set of uploaded chunks with the final list. """
        if self.is_complete():
            return
        self._to_upload = set(range(self.chunk_count)) - set(self.blob.uploadedChunkIds)

    def is_complete(self):
        # type: () -> bool
        return len(self.blob.uploadedChunkIds) == self.chunk_count

    def iter_upload(self):
        # type: () -> Generator
        """
        Get a generator to upload the file.

        If the `Uploader` has a callback, it is run after each chunk upload.
        The method will yield after the callback step. It yields the uploader
        itself since it contains all relevant data.
        """
        with self.blob as src:

            while self._to_upload:
                # Get the index of a chunk to upload
                index = self._to_upload.pop()
                # Seek to the right position
                src.seek(index * self.chunk_size)
                # Read a chunk of data
                data = src.read(self.chunk_size)
                # Upload it
                self.process(self.service.send_data(
                    self.blob.name, data, self.path, self.chunked, index, self.headers
                ))
                # If the set of chunks to upload is empty, check whether
                # the server has received all of them.
                if not self._to_upload:
                    self._compute_chunks_left()
                # Call the callback if it exists
                if callable(self.callback):
                    self.callback(self)
                # Yield to the upper scope
                yield self

        self._update_batch()

    def process(self, response):
        # type: (Blob) -> None
        super(ChunkUploader, self).process(response)
        self.blob.uploadedChunkIds = response.uploadedChunkIds

    def upload(self):
        # type: () -> None
        list(self.iter_upload())
