from abc import ABC, abstractmethod

from app.connectors.schemas import ConnectorManifest, ConnectorSyncResult


class BaseConnector(ABC):
    connector_id: str
    name: str
    type: str
    description: str
    status: str = "available"
    auth_type: str = "none"
    supported_data_types: list[str] = []

    def manifest(self) -> ConnectorManifest:
        return ConnectorManifest(
            connector_id=self.connector_id,
            name=self.name,
            type=self.type,
            description=self.description,
            status=self.status,
            auth_type=self.auth_type,
            supported_data_types=self.supported_data_types,
        )

    def test_connection(self, config: dict, auth: dict | None = None) -> dict:
        return {"status": "connected", "message": f"{self.name} connector is available."}

    @abstractmethod
    def sync(self, connector_id: int, config: dict, auth: dict | None = None, *, sync_type: str = "manual") -> ConnectorSyncResult:
        raise NotImplementedError

    def get_schema(self) -> dict:
        return {"config": {}, "auth": {}}

    def get_last_sync_status(self) -> dict:
        return {"status": "not_synced"}
