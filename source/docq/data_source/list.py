"""List of all data sources supported by DocQ."""

from .aws_s3 import AwsS3
from .azure_blob import AzureBlob
from .manual_upload import ManualUpload

SPACE_DATA_SOURCES = {
    "MANUAL_UPLOAD": ManualUpload(),
    "AZURE_BLOB": AzureBlob(),
    "AWS_S3": AwsS3(),
}
