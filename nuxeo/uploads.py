# coding: utf-8
from __future__ import unicode_literals

from .compat import quote, text
from .endpoint import APIEndpoint
from .models import Batch, Blob
from .utils import SwapAttr

try:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from typing import Any, Dict, List, Optional, Text, Union
        from .client import NuxeoClient
except ImportError:
    pass

CHUNK_LIMIT = 10 * 1024 * 1024
MAX_RETRY = 3


class API(APIEndpoint):
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
        return resource

    def post(self):
        # type: () -> Batch
        """
        Create a batch.

        :return: the created batch
        """
        with SwapAttr(self, '_cls', Batch):
            batch = super(API, self).post()
        return batch

    batch = post  # Alias for clarity

    def put(self, **kwargs):
        # type: (Any) -> None
        raise NotImplementedError

    def delete(self, batch_id, file_idx=None):
        # type: (Text, Optional[int]) -> None
        """
        Delete a batch or a blob.

        If the file_idx is None, deletes the batch,
        otherwise deletes the corresponding blob.

        :param batch_id: the id of the batch
        :param file_idx: the index of the blob
        :return: the deleted batch, or None for a blob
        """
        if file_idx:
            target = '{}/{}'.format(batch_id, file_idx)
            super(API, self).delete(target)
        else:
            target = batch_id
            with SwapAttr(self, '_cls', Batch):
                super(API, self).delete(target)

    def upload(self, batch, blob, chunked=False, limit=CHUNK_LIMIT):
        # type: (Batch, Blob) -> Blob
        """
        Upload a blob.

        :param batch: batch of the upload
        :param blob: blob to upload
        :param chunked: if True, send in chunks
        :param limit: if blob is bigger, send in chunks
        :return: uploaded blob details
        """
        chunked = chunked or blob.size > limit

        headers = self.headers
        headers.update({
            'Cache-Control': 'no-cache',
            'X-File-Name': quote(blob.name),
            'X-File-Size': text(blob.size),
            'X-File-Type': blob.mimetype,
            'Content-Length': text(blob.size),
        })

        path = '{}/{}'.format(batch.batchId, batch.upload_idx)

        if chunked:
            info = super(API, self).get(path, default=None)

            if info and (info.uploadType == 'normal'
                         or len(info.uploadedChunkIds) == info.chunkCount):
                return info  # All the chunks have been uploaded

            if info:
                chunk_count = info.chunkCount
                chunk_size = info.size // chunk_count + (info.size % chunk_count > 0)
                index = info.uploadedChunkIds[-1] + 1
            else:  # It's a new upload
                chunk_size = self.client.chunk_size
                chunk_count = blob.size // chunk_size + (blob.size % chunk_size > 0)
                index = 0

            headers.update({
                'X-Upload-Type': 'chunked',
                'X-Upload-Chunk-Count': text(chunk_count),
                'Content-Length': text(chunk_size)
            })
        else:
            index, chunk_count = 0, 1
            chunk_size = blob.size or None

        with blob as source:
            if index:
                source.seek(index * chunk_size)
            while index < chunk_count:
                data = source.read(chunk_size)
                if not data:
                    break

                if chunked:
                    headers['X-Upload-Chunk-Index'] = text(index)

                for i in range(MAX_RETRY):
                    response = super(API, self).post(
                        resource=data,
                        path=path,
                        raw=True,
                        headers=headers,
                        default=None
                    )
                    if response:
                        break

                if not response:
                    raise ConnectionError('Unable to upload chunk.')
                index += 1

        batch.upload_idx += 1
        response.batch_id = batch.uid
        return response
