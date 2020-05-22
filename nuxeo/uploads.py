# coding: utf-8
from __future__ import unicode_literals

from .compat import text
from .constants import UPLOAD_CHUNK_SIZE, UP_AMAZON_S3
from .endpoint import APIEndpoint
from .exceptions import HTTPError, InvalidUploadHandler, UploadError
from .models import Batch, Blob
from .utils import SwapAttr, chunk_partition

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import (
            Any,
            BinaryIO,
            Callable,
            Dict,
            List,
            Optional,
            Text,
            Tuple,
            Union,
        )
        from .client import NuxeoClient
        from .models import BufferBlob, FileBlob
        from .handlers.default import Uploader

        ActualBlob = Union[BufferBlob, FileBlob]
except ImportError:
    pass


class API(APIEndpoint):
    """ Endpoint for uploads. """

    def __init__(self, client, endpoint="upload", headers=None):
        # type: (NuxeoClient, Text, Optional[Dict[Text, Text]]) -> None
        super(API, self).__init__(client, endpoint=endpoint, cls=Blob, headers=headers)

        # Available upload handlers
        self.__handlers = None  # type: Optional[List[str]]

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
            path = "{}/{}".format(path, file_idx)

        resource = super(API, self).get(path=path)

        if file_idx is not None:
            resource.batch_id = batch_id
            resource.fileIdx = file_idx
        elif not resource:
            return []
        return resource

    def post(self, handler=""):
        # type: (Optional[Text]) -> Batch
        """
        Create a batch.

        :param handler: the upload handler to use
        :return: the created batch
        """
        endpoint = self.endpoint
        if handler:
            handler = handler.lower()
            handlers = self.handlers()
            if handler in handlers:
                if handler != "default":
                    endpoint = "{}/new/{}".format(endpoint, handler)
            else:
                raise InvalidUploadHandler(handler, handlers)

        response = self.client.request("POST", endpoint)
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
            target = "{}/{}".format(batch_id, file_idx)
            super(API, self).delete(target)
        else:
            target = batch_id
            with SwapAttr(self, "_cls", Batch):
                super(API, self).delete(target)

    def handlers(self, force=False):
        # type: (Optional[bool]) -> List[str]
        """
        Get available upload handlers.

        :param force: force refreshing the list
        """
        if self.__handlers is None or force:
            endpoint = "{}/handlers".format(self.endpoint)
            try:
                response = self.client.request("GET", endpoint)
                self.__handlers = [h for h in response.json()["handlers"][0].values()]
            except Exception:
                # This is not good, no handlers == no uploads!
                # Return an empty list without modifying .__handlers
                # to force a new HTTP call the next time.
                return []
        return self.__handlers

    def has_s3(self):
        # type: () -> bool
        """Return True if the Amazon S3 upload provider is available."""
        return UP_AMAZON_S3 in self.handlers()

    def send_data(
        self,
        name,  # type: Text
        data,  # type: Union[BinaryIO, Text, bytes]
        path,  # type: Text
        chunked,  # type: bool
        index,  # type: int
        headers,  # type: Dict[Text, Text]
        data_len=0,  # type: Optional[int]
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
            headers["X-Upload-Chunk-Index"] = text(index)

        if data_len > 0:
            headers["Content-Length"] = text(data_len)

        try:
            return super(API, self).post(
                resource=data, path=path, raw=True, headers=headers
            )
        except HTTPError as e:
            raise UploadError(name, chunk=index if chunked else None, info=str(e))

    def state(self, path, blob, chunk_size=UPLOAD_CHUNK_SIZE):
        # type: (Text, ActualBlob, int) -> Tuple[int, List[int]]
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
        :return: a tuple of the chunk count and
                 the set of uploaded chunk indexes
        """
        info = super(API, self).get(path, default=None)

        if info:
            chunk_count = int(info.chunkCount)
            uploaded_chunks = [int(i) for i in info.uploadedChunkIds]
        else:
            # It's a new upload
            chunk_count, _ = chunk_partition(blob.size, chunk_size)
            uploaded_chunks = []

        return chunk_count, uploaded_chunks

    def upload(
        self,
        batch,  # type: Batch
        blob,  # type: ActualBlob
        chunked=False,  # type: bool
        chunk_size=UPLOAD_CHUNK_SIZE,  # type: int
        callback=None,  # type: Union[Callable, Tuple[Callable]]
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
        :param callback: if not None, they are executed between each chunk.
          It is either a single callable or a tuple of callables (tuple is used to keep order).
        :return: uploaded blob details
        """
        uploader = self.get_uploader(
            batch, blob, chunked, chunk_size, callback=callback
        )
        uploader.upload()
        return uploader.blob

    def execute(self, batch, operation, file_idx=None, params=None, void_op=True):
        # type: (Batch, Text, Optional[int], Optional[Dict[Text,Any]], bool) -> Any
        """
        Execute an operation with the batch or one of its files as an input.

        :param batch: input for the operation
        :param operation: operation to execute
        :param file_idx: if not None, sole input of the operation
        :param params: parameters for the operation
        :param void_op: if True, the body of the response
        from the server will be empty
        :return: the output of the operation
        """
        path = "{}/{}".format(self.endpoint, batch.uid)
        if file_idx is not None:
            path = "{}/{}".format(path, file_idx)

        path = "{}/execute/{}".format(path, operation)

        headers = {}
        if void_op:
            headers = {"X-NXVoidOperation": "true"}

        return self.client.request(
            "POST", path, data={"params": params}, headers=headers or None
        )

    def attach(self, batch, doc, file_idx=None):
        # type: (Batch, Text, Optional[int]) -> Any
        """
        Attach one or all files of a batch to a document.

        :param batch: batch to attach
        :param doc: document to attach
        :param file_idx: if not None, only this file will be attached
        :return: the output of the attach operation
        """
        params = {"document": doc}
        if file_idx is None and batch.upload_idx > 1:
            params["xpath"] = "files:files"
        return self.execute(batch, "Blob.Attach", file_idx, params)

    def complete(self, batch, **kwargs):
        # type: (Batch, Any) -> Any
        """
        Complete an upload.
        This is a no-op when using the default upload provider.

        :param batch: batch to complete
        :param kwargs: additional arguments fowarded at the underlying level
        :return: the output of the complete operation
        """
        if batch.provider == UP_AMAZON_S3:
            blob = batch.blobs[0]
            s3_info = batch.extraInfo
            params = {
                "name": blob.name,
                "fileSize": blob.size,
                "key": "{}/{}".format(s3_info["baseKey"].rstrip("/"), blob.name),
                "bucket": s3_info["bucket"],
                "etag": batch.etag,
            }
            endpoint = "{}/{}/{}/complete".format(
                self.endpoint, batch.uid, batch.upload_idx - 1
            )
            return self.client.request("POST", endpoint, data=params, **kwargs)

        # Doing a /complete with the default upload provider
        # will end on a HTTP 409 Conflict error.
        return None

    def get_uploader(
        self,
        batch,  # type: Batch
        blob,  # type: ActualBlob
        chunked=False,  # type: bool
        chunk_size=UPLOAD_CHUNK_SIZE,  # type: int
        callback=None,  # type: Union[Callable, Tuple[Callable]]
    ):
        # type: (...) -> "Uploader"
        """
        Get an upload helper for blob.

        Can be used to upload a new blob or resume
        the upload of a chunked blob.

        :param batch: batch of the upload
        :param blob: blob to upload
        :param chunked: if True, send in chunks
        :param chunk_size: if blob is bigger, send in chunks of this size
        :param callback: if not None, they are executed between each chunk.
          It is either a single callable or a tuple of callables (tuple is used to keep order).
        :return: uploaded blob details
        """
        chunked = chunked and blob.size > chunk_size

        if batch.provider == UP_AMAZON_S3:
            if chunked:
                from .handlers.s3 import ChunkUploaderS3 as cls
            else:
                from .handlers.s3 import UploaderS3 as cls
        else:
            if chunked:
                from .handlers.default import ChunkUploader as cls
            else:
                from .handlers.default import Uploader as cls

        return cls(self, batch, blob, chunk_size, callback)

    def refresh_token(self, batch, **kwargs):
        # type: (Batch, Any) -> Dict[str, Any]
        """
        Get fresh tokens for the given batch.
        The *Batch.extraInfo* dict will be updated inplace with the new data.

        If the server is outdated and does not contain the refreshToken API, then
        *Batch.extraInfo* will be returned to prevent a HTTP 404 error.
        This is done on purpose and finally the ExpiredToken error will be raised
        by boto3.

        This is a no-op when using the default upload provider.

        :param batch: the targeted batch
        :param kwargs: additional arguments forwarded at the underlying level
        :return: a dict containing new tokens
        """
        # Return an empty dict by default instead of raising an error.
        # It is more convenient.
        creds = {}

        if batch.provider:
            endpoint = "{}/{}/refreshToken".format(self.endpoint, batch.uid)
            req = self.client.request("POST", endpoint, default=None, **kwargs)
            if req:
                creds = req.json()
                batch.extraInfo.update(**creds)
            else:
                # Allow outdated servers (without the refreshToken API) to still work with S3.
                # It will just end on a ExpiredToken error, but it is better than a 404 error.
                creds = batch.extraInfo

        return creds
