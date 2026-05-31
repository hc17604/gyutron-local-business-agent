from pydantic import BaseModel


DATA_TYPES = ["inquiry", "order", "product", "inventory", "advertising", "customer", "sales_followup", "report"]


class ConnectorManifest(BaseModel):
    connector_id: str
    name: str
    type: str
    description: str
    status: str
    auth_type: str
    supported_data_types: list[str]


class ConnectorSyncResult(BaseModel):
    records_found: int = 0
    records_imported: int = 0
    summary: str = ""
    imported_files: list[str] = []
