from app.connectors.base import BaseConnector
from app.connectors.schemas import DATA_TYPES, ConnectorSyncResult


class MockPlatformConnector(BaseConnector):
    status = "mock"
    auth_type = "oauth_placeholder"
    supported_data_types = DATA_TYPES

    def sync(self, connector_id: int, config: dict, auth: dict | None = None, *, sync_type: str = "manual") -> ConnectorSyncResult:
        return ConnectorSyncResult(summary=f"{self.name} is a mock connector. Real API sync is not enabled in MVP.")


class MockAlibabaConnector(MockPlatformConnector):
    connector_id = "alibaba"
    name = "Alibaba"
    type = "alibaba"
    description = "Placeholder for future Alibaba Open Platform integration."


class MockShopeeConnector(MockPlatformConnector):
    connector_id = "shopee"
    name = "Shopee"
    type = "shopee"
    description = "Placeholder for future Shopee integration."


class MockAmazonConnector(MockPlatformConnector):
    connector_id = "amazon"
    name = "Amazon"
    type = "amazon"
    description = "Placeholder for future Amazon SP-API integration."


class MockShopifyConnector(MockPlatformConnector):
    connector_id = "shopify"
    name = "Shopify"
    type = "shopify"
    description = "Placeholder for future Shopify integration."
