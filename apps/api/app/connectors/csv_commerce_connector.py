"""CSV commerce connector — the second real adapter (and the replication proof).

Imports orders / order_items / customers / payments CSV exports into the
unified commerce model. Everything is mapping-driven (connectors/csv_mappings.py);
a new platform or a new mock customer = a new config, zero importer changes.

config_json:
  source_key    e.g. "acme-industrial-csv"  (REQUIRED — the commerce `source`)
  display_name  e.g. "ACME Industrial (CSV)"
  folder_path   folder containing orders.csv / order_items.csv / customers.csv / payments.csv (any subset)
  mapping       "generic" (default) | "shopify"

Idempotent: (source, external_id) upsert — re-importing the same file changes
nothing. Bad rows are skipped and reported with line numbers, never fail the run.
"""
import csv
from datetime import datetime, timezone
from pathlib import Path

from app.connectors.base import BaseConnector
from app.connectors.csv_mappings import MAPPINGS
from app.connectors.local_folder_connector import resolve_allowed_folder
from app.connectors.schemas import ConnectorSyncResult
from app.database import get_connection
from app.services.commerce_store import (
    canonical_order_status, canonical_payment_status, ensure_source, to_base, upsert,
)


FILE_TO_TABLE = {"orders": "orders", "order_items": "order_items", "customers": "customers", "payments": "payments"}
STATUS_FNS = {"order": canonical_order_status, "payment": canonical_payment_status}


def _coerce(value: str, kind: str):
    value = (value or "").strip()
    if value == "":
        return None
    if kind == "float":
        return float(value.replace(",", "").replace("$", "").replace("€", ""))
    if kind == "int":
        return int(float(value.replace(",", "")))
    if kind == "date":
        v = value.replace("Z", "+00:00")
        for fmt in (None, "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                dt = datetime.fromisoformat(v) if fmt is None else datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            except ValueError:
                continue
        raise ValueError(f"unparseable date: {value!r}")
    return value


class CsvCommerceConnector(BaseConnector):
    connector_id = "csv_commerce"
    name = "CSV Commerce Import"
    type = "csv_commerce"
    description = "Imports orders / items / customers / payments CSV exports (generic or Shopify format) into the unified commerce model. One mapping config per platform."
    status = "available"
    auth_type = "none"
    supported_data_types = ["order", "customer", "product"]

    def test_connection(self, config: dict, auth: dict | None = None) -> dict:
        try:
            folder = resolve_allowed_folder(config.get("folder_path", ""))
        except Exception as exc:
            return {"status": "error", "message": f"Folder not allowed/found: {exc}"}
        mapping_id = config.get("mapping", "generic")
        if mapping_id not in MAPPINGS:
            return {"status": "error", "message": f"Unknown mapping: {mapping_id}"}
        if not config.get("source_key"):
            return {"status": "error", "message": "config.source_key is required (commerce source identity)."}
        found = [k for k in FILE_TO_TABLE if (folder / f"{k}.csv").exists()]
        return {"status": "connected", "message": f"Folder OK ({folder}); files: {', '.join(found) or 'none yet'}; mapping={mapping_id}."}

    def sync(self, connector_id: int, config: dict, auth: dict | None = None, *, sync_type: str = "manual") -> ConnectorSyncResult:
        folder = resolve_allowed_folder(config.get("folder_path", ""))
        mapping = MAPPINGS[config.get("mapping", "generic")]
        source_key = config["source_key"]
        ensure_source(source_key, config.get("display_name") or source_key, "csv-commerce", connector_id)

        found = imported = 0
        skipped: list[str] = []
        with get_connection() as connection:
            for file_kind, table in FILE_TO_TABLE.items():
                path = folder / f"{file_kind}.csv"
                spec = mapping["files"].get(file_kind)
                if not path.exists() or spec is None:
                    continue
                f, i, s = self._import_file(connection, path, file_kind, table, spec, source_key)
                found += f
                imported += i
                skipped.extend(s)
            connection.commit()

        summary = f"Imported {imported}/{found} rows from {folder.name} (source={source_key})"
        if skipped:
            summary += f"; skipped {len(skipped)}: " + "; ".join(skipped[:5])
        return ConnectorSyncResult(records_found=found, records_imported=imported, summary=summary)

    @staticmethod
    def _import_file(connection, path: Path, file_kind: str, table: str, spec: dict, source_key: str):
        found = imported = 0
        skipped: list[str] = []
        with open(path, encoding="utf-8-sig", newline="") as handle:
            for line_no, row in enumerate(csv.DictReader(handle), start=2):
                found += 1
                try:
                    ext_col = spec["external_id"]["col"]
                    external_id = (row.get(ext_col) or "").strip()
                    if not external_id:
                        raise ValueError(f"missing {ext_col}")
                    columns: dict = {}
                    for field, rule in spec["columns"].items():
                        value = _coerce(row.get(rule["col"], ""), rule.get("type", "str"))
                        if value is None and rule.get("required"):
                            raise ValueError(f"missing {rule['col']}")
                        if value is not None:
                            columns[field] = value
                    # canonical status + base-currency derivation
                    status_fn = STATUS_FNS.get(spec.get("status_map", ""))
                    if status_fn:
                        columns["status"] = status_fn(columns.get("raw_status"))
                    amount = columns.get("total_amount", columns.get("amount", columns.get("unit_amount")))
                    if amount is not None:
                        columns["amount_base"] = to_base(amount, columns.get("currency"))
                    upsert(connection, table, source_key, external_id, columns, dict(row))
                    imported += 1
                except (ValueError, KeyError) as exc:
                    skipped.append(f"{file_kind}.csv:{line_no} {exc}")
        return found, imported, skipped
