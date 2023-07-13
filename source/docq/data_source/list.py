"""List of all data sources supported by Docq."""

from ..config import SpaceDataSourceType
from .aws_s3 import AwsS3
from .azure_blob import AzureBlob
from .manual_upload import ManualUpload
from .web_scraper import WebScraper

SPACE_DATA_SOURCES = {
    SpaceDataSourceType.MANUAL_UPLOAD.name: ManualUpload(),
    SpaceDataSourceType.AZURE_BLOB.name: AzureBlob(),
    SpaceDataSourceType.AWS_S3.name: AwsS3(),
    SpaceDataSourceType.WEB_SCRAPER.name: WebScraper(),
}
