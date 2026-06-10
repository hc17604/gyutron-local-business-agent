from app.connectors.base import BaseConnector
from app.connectors.csv_commerce_connector import CsvCommerceConnector
from app.connectors.excel_csv_connector import ExcelCsvConnector
from app.connectors.gyutron_website_connector import GyutronWebsiteConnector
from app.connectors.local_folder_connector import LocalFolderConnector
from app.connectors.mock_platforms import MockAlibabaConnector, MockAmazonConnector, MockShopeeConnector, MockShopifyConnector


CONNECTORS: dict[str, BaseConnector] = {
    "excel_csv": ExcelCsvConnector(),
    "local_folder": LocalFolderConnector(),
    "gyutron_website": GyutronWebsiteConnector(),
    "csv_commerce": CsvCommerceConnector(),
    "alibaba": MockAlibabaConnector(),
    "shopee": MockShopeeConnector(),
    "amazon": MockAmazonConnector(),
    "shopify": MockShopifyConnector(),
}


def get_connector(connector_type: str) -> BaseConnector:
    if connector_type not in CONNECTORS:
        raise KeyError(f"Unknown connector type: {connector_type}")
    return CONNECTORS[connector_type]


def list_manifests() -> list[dict]:
    return [connector.manifest().dict() for connector in CONNECTORS.values()]
