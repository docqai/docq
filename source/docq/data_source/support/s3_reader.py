"""S3 file and directory reader.

A loader that fetches a file or iterates through a directory on AWS S3.

"""
import logging as log
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import boto3
from botocore.exceptions import ClientError
from llama_index import SimpleDirectoryReader
from llama_index.readers.base import BaseReader
from llama_index.readers.schema.base import Document

from ..main import DocumentMetadata


class S3Reader(BaseReader):
    """General reader for any S3 file or directory."""
    _s3_client = None

    def __init__(  # noqa: D417
        self,
        *args: Optional[Any],
        bucket: str,
        region: str,
        key: Optional[str] = None,
        prefix: Optional[str] = "",
        file_extractor: Optional[Dict[str, Union[str, BaseReader]]] = None,
        required_exts: Optional[List[str]] = None,
        filename_as_id: bool = False,
        num_files_limit: Optional[int] = None,
        file_metadata: Optional[Callable[[str], Dict]] = None,
        aws_access_id: Optional[str] = None,
        aws_access_secret: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        s3_endpoint_url: Optional[str] = "https://s3.amazonaws.com",
        **kwargs: Optional[Any],
    ) -> None:
        """Initialize S3 bucket and key, along with credentials if needed.

        If key is not set, the entire bucket (filtered by prefix) is parsed.

        Args:
        bucket (str): the name of your S3 bucket
        key (Optional[str]): the name of the specific file. If none is provided,
            this loader will iterate through the entire bucket.
        prefix (Optional[str]): the prefix to filter by in the case that the loader
            iterates through the entire bucket. Defaults to empty string.
        file_extractor (Optional[Dict[str, BaseReader]]): A mapping of file
            extension to a BaseReader class that specifies how to convert that file
            to text. See `SimpleDirectoryReader` for more details.
        required_exts (Optional[List[str]]): List of required extensions.
            Default is None.
        num_files_limit (Optional[int]): Maximum number of files to read.
            Default is None.
        file_metadata (Optional[Callable[str, Dict]]): A function that takes
            in a filename and returns a Dict of metadata for the Document.
            Default is None.
        aws_access_id (Optional[str]): provide AWS access key directly.
        aws_access_secret (Optional[str]): provide AWS access key directly.
        s3_endpoint_url (Optional[str]): provide S3 endpoint URL directly.
        """
        super().__init__(*args, **kwargs)

        self.bucket = bucket
        self.region = region
        self.key = key
        self.prefix = prefix

        self.file_extractor = file_extractor
        self.required_exts = required_exts
        self.filename_as_id = filename_as_id
        self.num_files_limit = num_files_limit
        self.file_metadata = file_metadata

        self.aws_access_id = aws_access_id
        self.aws_access_secret = aws_access_secret
        self.aws_session_token = aws_session_token
        self.s3_endpoint_url = s3_endpoint_url
        self.extra_metadata = {}

    def _generate_presigned_url(self, s3_client: Any, key: str) -> str:  # noqa: ANN401
        """Generate blob presigned url."""
        try:
            return s3_client.generate_presigned_url(
                'get_object',
                Params = {'Bucket': self.bucket, 'Key': key},
                ExpiresIn = (60 * 60 * 24 * 7 * 1) - 1, # 1 week
            )
        except ClientError as e:
            log.error(e)
            return None

    def _set_metadata(self, key: str, path: str) -> None:
        blob_url = self._generate_presigned_url(self._s3_client, key)
        self.extra_metadata[path] = {
            DocumentMetadata.SOURCE_URI.name: blob_url,
            "file_name": key,
        }

    def _load_metadata(self, key: str) -> Dict[str, Any]:
        """Load metadata."""
        if self.file_metadata:
            return { **self.file_metadata(key), **self.extra_metadata.get(key) }
        return self.extra_metadata.get(key)

    def load_data(self) -> List[Document]:
        """Load file(s) from S3."""
        session = boto3.Session(
            aws_access_key_id=self.aws_access_id,
            aws_secret_access_key=self.aws_access_secret,
            region_name=self.region,
            #aws_session_token=self.aws_session_token,
        )
        s3 = session.resource("s3")
        s3_client = session.client("s3") #, endpoint_url=self.s3_endpoint_url)
        self._s3_client = s3_client
        with tempfile.TemporaryDirectory() as temp_dir:
            if self.key:
                suffix = Path(self.key).suffix
                filepath = f"{temp_dir}/{next(tempfile._get_candidate_names())}{suffix}"
                s3_client.download_file(self.bucket, self.key, filepath)
                self._set_metadata(self.key, filepath)
            else:
                bucket = s3.Bucket(self.bucket)
                print(f"\x1b[31m Debug bucket {bucket} \x1b[0m")
                for i, obj in enumerate(bucket.objects.filter(Prefix=self.prefix)):
                    print(f"\x1b[31m Debug obj {obj} \x1b[0m")
                    if self.num_files_limit is not None and i > self.num_files_limit:
                        break

                    suffix = Path(obj.key).suffix

                    is_dir = obj.key.endswith("/") # skip folders
                    is_bad_ext = (
                        self.required_exts is not None and suffix not in self.required_exts # skip other extentions
                    )

                    if is_dir or is_bad_ext:
                        continue

                    filepath = (
                        f"{temp_dir}/{next(tempfile._get_candidate_names())}{suffix}"
                    )
                    try:
                        s3_client.download_file(self.bucket, obj.key, filepath)
                        self._set_metadata(obj.key, filepath)
                        print(f"\x1b[31m Blob download compleated {obj.key} \x1b[0m")
                    except ClientError as e:
                        print(f"\x1b[31m Error downloading blob {e} \x1b[0m")
                        log.error("Error process %s", e)
            loader = SimpleDirectoryReader(
                temp_dir,
                file_extractor=self.file_extractor,
                file_metadata=self._load_metadata,
            )

            return loader.load_data()
