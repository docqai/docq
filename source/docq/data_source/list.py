"""List of all data sources supported by Docq."""

from enum import Enum

from .aws_s3 import AwsS3
from .azure_blob import AzureBlob
from .knowledge_base_scraper import KnowledgeBaseScraper
from .main import DataSource
from .manual_upload import ManualUpload
from .web_scraper import WebScraper

# SPACE_DATA_SOURCES = {
#     SpaceDataSourceType.MANUAL_UPLOAD.name: ManualUpload(),
#     SpaceDataSourceType.AZURE_BLOB.name: AzureBlob(),
#     SpaceDataSourceType.AWS_S3.name: AwsS3(),
#     SpaceDataSourceType.WEB_SCRAPER.name: WebScraper(),
#     SpaceDataSourceType.KNOWLEDGE_BASE_SCRAPER.name: KnowledgeBaseScraper(),
# }


class SpaceDataSources(Enum):
    """Space datasource list."""

    MANUAL_UPLOAD: DataSource = DataSource(ManualUpload())
    AZURE_BLOB: DataSource = DataSource(AzureBlob())
    AWS_S3: DataSource = DataSource(AwsS3())
    WEB_SCRAPER: DataSource = DataSource(WebScraper())
    KNOWLEDGE_BASE_SCRAPER: DataSource = DataSource(KnowledgeBaseScraper())
