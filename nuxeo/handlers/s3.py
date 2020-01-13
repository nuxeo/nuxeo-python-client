# coding: utf-8
"""
The Amazon S3 upload handler.
"""
from __future__ import unicode_literals

import logging

import boto3

from .default import Uploader
from ..constants import UP_AMAZON_S3
from ..exceptions import UploadError
from ..utils import chunk_partition, log_chunk_details

try:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any, Generator, List, Set, Tuple  # noqa
except ImportError:
    pass


logger = logging.getLogger(__name__)


class UploaderS3(Uploader):
    """ Helper for uploads using Amazon S3 Direct Upload (single). """

    def __init__(self, *args, **kwargs):
        # Allow to pass a custom S3 client (for tests)
        s3_client = kwargs.pop("s3_client", None)

        super(UploaderS3, self).__init__(*args, **kwargs)

        # Instantiate the S3 client
        s3_info = self.batch.extraInfo
        self.bucket = s3_info["bucket"]
        self.key = "{}/{}".format(s3_info["baseKey"].rstrip("/"), self.blob.name)
        self.s3_client = s3_client or boto3.client(
            "s3",
            aws_access_key_id=s3_info["awsSecretKeyId"],
            aws_secret_access_key=s3_info["awsSecretAccessKey"],
            aws_session_token=s3_info["awsSessionToken"],
            region_name=s3_info["region"],
        )

    def upload(self):
        # type: () -> None
        """ Upload the file. """
        with self.blob as fd:
            try:
                # Note: we are using put_object() rather than upload_fileobj()
                # to be able to retrieve the ETag from the response. The latter
                # returns nothing and it would involve doing another HTTP call
                # just to get that information.
                response = self.s3_client.put_object(
                    Bucket=self.bucket, Key=self.key, Body=fd
                )
            except Exception as e:
                raise UploadError(self.blob.path, info=str(e))

            # Save the ETag for the batch.complete() call
            self.batch.etag = response["ETag"]

        self.blob.uploadedSize = self.blob.size
        setattr(self, "_completed", True)

        for callback in self.callback:
            callback(self)

        self._update_batch()


class ChunkUploaderS3(UploaderS3):
    """ Helper for chunked uploads using Amazon S3 Direct Upload (multipart). """

    chunked = True

    def __init__(self, *args, **kwargs):
        # type: (Any, Any) -> None

        # Allow to use a custom *MaxParts* value, used in .state() (for tests)
        # 0 <= MaxParts <= 2,147,483,647 (default is 1,000)
        self._max_parts = kwargs.pop("max_parts", 1000)

        super(ChunkUploaderS3, self).__init__(*args, **kwargs)

        # Parts already sent
        self._data_packs = []

        self.chunk_count, self.blob.uploadedChunkIds = self.state()
        log_chunk_details(self.chunk_count, self.chunk_size, self.blob.uploadedChunkIds)

        self.blob.chunkCount = self.chunk_count
        self.blob.uploadedSize = len(self.blob.uploadedChunkIds) * self.chunk_size

        self._to_upload = []
        self._compute_chunks_left()

    def new(self):
        """
        Instantiate a new multipart upload.

        :return: the multipart upload ID
        """
        mpu = self.s3_client.create_multipart_upload(Bucket=self.bucket, Key=self.key)
        self.batch.multiPartUploadId = mpu["UploadId"]
        return self.batch.multiPartUploadId

    def _state(self):
        # type: () -> List[int]
        """See .state()."""

        uploaded_chunks = []
        data_packs = []
        chunk_size = 0
        first = True

        # 0 <= PartNumberMarker <= 2,147,483,647
        part_number_marker = 0

        while "there are parts":
            info = self.s3_client.list_parts(
                Bucket=self.bucket,
                Key=self.key,
                UploadId=self.batch.multiPartUploadId,
                PartNumberMarker=part_number_marker,
                MaxParts=self._max_parts,
            )

            # Nothing was uploaded yet
            if "Parts" not in info:
                break

            for part in info["Parts"]:
                # Save the part size based on the first recieved part data
                if first:
                    chunk_size = part["Size"]
                    first = False

                index = part["PartNumber"]
                data_packs.append({"ETag": part["ETag"], "PartNumber": index})
                uploaded_chunks.append(index)

            # No more parts
            if not info["IsTruncated"]:
                break

            # TODO: part not yet tested/covered. Will be done with NXPY-147.
            # Next parts batch will start with that number
            part_number_marker = info["NextPartNumberMarker"]

        return chunk_size, uploaded_chunks, data_packs

    def state(self):
        # type: () -> Tuple[int, List]
        """
        Get the state of a multipart upload.

        If the blob upload has not begun yet, the server
        will return a 404 error, so we initialize the
        different values.
        If the blob upload is incomplete, we return the
        values the server sent us.

        :return: the chunk count and uploaded chunks
        """
        uploaded_chunks = None

        if self.batch.multiPartUploadId:
            try:
                self.chunk_size, uploaded_chunks, self._data_packs = self._state()
            except Exception:
                logger.warning("No multipart upload found with that ID", exc_info=True)

        if uploaded_chunks is None:
            # It's a new upload
            self.new()
            uploaded_chunks = []

        # *chunk_size* is overidden on purpose:
        # S3 has limitations and chunk size & count may be different from initial values
        chunk_count, self.chunk_size = chunk_partition(
            self.blob.size, self.chunk_size, handler=UP_AMAZON_S3
        )

        return chunk_count, uploaded_chunks

    def _compute_chunks_left(self):
        # type: () -> None
        """ Compare the set of uploaded chunks with the final list. """
        if self.is_complete():
            return

        # S3 starts counting at 1
        to_upload = set(range(1, self.chunk_count + 1, 1)) - set(
            self.blob.uploadedChunkIds
        )
        self._to_upload = sorted(list(to_upload))

    def is_complete(self):
        # type: () -> bool
        """Return True when the upload is completely done."""
        return len(self.blob.uploadedChunkIds) == self.chunk_count

    def iter_upload(self):
        # type: () -> Generator
        """Upload a file in chunks.

        If the `Uploader` has callback(s), they are run after each chunk upload.
        The method will yield after the callbacks step. It yields the uploader
        itself since it contains all relevant data.
        The method will also yield before starting the upload to be able to store
        AWS credentials and the multipart upload ID.
        """

        # Yield now to allow the caller to save AWS credentials and the MPU ID
        yield self

        with self.blob as fd:
            while self._to_upload:
                # Get the index of a chunk to upload
                part_number = self._to_upload[0]

                # Seek to the right position (S3 starts counting at 1)
                position = (part_number - 1) * self.chunk_size
                fd.seek(position)

                # Read a chunk of data
                data = fd.read(self.chunk_size)
                data_len = len(data)

                try:
                    # Upload it
                    part = self.s3_client.upload_part(
                        UploadId=self.batch.multiPartUploadId,
                        Bucket=self.bucket,
                        Key=self.key,
                        PartNumber=part_number,
                        Body=data,
                        ContentLength=data_len,
                    )
                except Exception as e:
                    raise UploadError(self.blob.path, chunk=part_number, info=str(e))

                # Now that the part is uploaded, remove it from the list
                self._to_upload.pop(0)

                self._data_packs.append(
                    {"ETag": part["ETag"], "PartNumber": part_number}
                )
                self.blob.uploadedChunkIds.append(part_number)
                self.blob.uploadedSize += data_len

                # If the set of chunks to upload is empty, check whether
                # the server has received all of them.
                if not self._to_upload:
                    self._compute_chunks_left()

                # Call the callback(s), if any
                for callback in self.callback:
                    callback(self)

                # Yield to the upper scope
                yield self

        # Complete the upload on the S3 side
        response = self.s3_client.complete_multipart_upload(
            Bucket=self.bucket,
            Key=self.key,
            UploadId=self.batch.multiPartUploadId,
            MultipartUpload={"Parts": self._data_packs},
        )

        # Save the ETag for the batch.complete() call
        self.batch.etag = response["ETag"]

        assert self.blob.uploadedSize == self.blob.size, "{:,d} != {:,d}".format(
            self.blob.uploadedSize, self.blob.size
        )

        self._update_batch()

    def upload(self):
        # type: () -> None
        """Helper to upload the file in one-shot."""
        list(self.iter_upload())
