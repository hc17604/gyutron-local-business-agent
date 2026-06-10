"""GYUTRON Website connector — the first REAL API data source.

Pulls leads / RFQs / support requests / download requests / events from the
GYUTRON website's read-only Data API over HTTPS (Bearer key). It NEVER touches
the website database — the API contract (docs/data-api-contract.md in the
website repo) is the integration boundary, so this class doubles as the
template for future customer connectors.

Incremental sync model: the API pages with `cursor` (internal id) WITHIN one
run and filters with `since` (created_at, inclusive) ACROSS runs. We persist a
per-resource `since` watermark in `connector_state` and de-duplicate overlap
rows by upserting on (connector_id, data_type, external_id).

Auth: the API key is read from the GYUTRON_WEBSITE_API_KEY environment
variable at call time (never stored in config_json, which is exposed to the
frontend; never logged).
"""
import json
import os

import httpx

from app.connectors.base import BaseConnector
from app.connectors.schemas import ConnectorSyncResult
from app.database import get_connection


DEFAULT_BASE_URL = "https://www.gyutron.com"
PAGE_LIMIT = 200
MAX_PAGES_PER_RESOURCE = 50  # safety backstop against runaway pagination

# (local data_type, API resource path segment)
RESOURCES: list[tuple[str, str]] = [
    ("lead", "leads"),
    ("rfq", "rfqs"),
    ("support_request", "support-requests"),
    ("download_request", "download-requests"),
    ("event", "events"),
]


class GyutronWebsiteError(RuntimeError):
    """Sync failed (network / server error)."""


class GyutronWebsiteAuthError(GyutronWebsiteError):
    """API key missing or rejected."""


class GyutronWebsiteConnector(BaseConnector):
    connector_id = "gyutron_website"
    name = "GYUTRON Website"
    type = "gyutron_website"
    description = "Website leads, RFQs, support/download requests and the event stream via the read-only GYUTRON Data API (HTTPS, Bearer key)."
    status = "available"
    auth_type = "api_key"
    supported_data_types = ["inquiry"]

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        # Tests inject an httpx.MockTransport here; production uses the default.
        self._transport = transport

    # ------------------------------ config --------------------------------
    @staticmethod
    def _api_key(config: dict | None = None) -> str:
        # Per-connector key env var (multi-customer): config.api_key_env names the
        # variable; the VALUE always stays in the environment, never in config_json.
        env_var = (config or {}).get("api_key_env") or "GYUTRON_WEBSITE_API_KEY"
        return os.environ.get(env_var, "").strip()

    @staticmethod
    def _base_url(config: dict | None) -> str:
        return ((config or {}).get("base_url") or os.environ.get("GYUTRON_WEBSITE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")

    def _client(self, config: dict | None) -> httpx.Client:
        headers = {}
        key = self._api_key(config)
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return httpx.Client(base_url=self._base_url(config), headers=headers, timeout=20.0, transport=self._transport)

    def get_schema(self) -> dict:
        return {
            "config": {"base_url": {"type": "string", "default": DEFAULT_BASE_URL, "description": "Data API origin"}},
            "auth": {"api_key": {"type": "env", "env_var": "GYUTRON_WEBSITE_API_KEY", "description": "Bearer key for GET /api/v1/* (set in the environment, not stored)"}},
        }

    # --------------------------- test connection ---------------------------
    def test_connection(self, config: dict, auth: dict | None = None) -> dict:
        try:
            with self._client(config) as client:
                health = client.get("/api/v1/health")
                health.raise_for_status()
                health_body = health.json()
                if not self._api_key(config):
                    return {
                        "status": "error",
                        "message": f"Health OK, but {(config or {}).get('api_key_env') or 'GYUTRON_WEBSITE_API_KEY'} is not set in the environment — metadata/resources need it.",
                    }
                meta = client.get("/api/v1/metadata")
                if meta.status_code in (401, 403):
                    return {"status": "error", "message": f"API key rejected ({meta.status_code}). Check GYUTRON_WEBSITE_API_KEY."}
                meta.raise_for_status()
                data = (meta.json() or {}).get("data") or {}
                source = (data.get("source") or {}).get("id") or health_body.get("source") or "unknown"
                counts = data.get("counts") or {}
                counts_text = ", ".join(f"{k}={v}" for k, v in counts.items()) if counts else "no counts reported"
                return {"status": "connected", "message": f"Connected to {source}. Rows: {counts_text}."}
        except httpx.HTTPError as exc:
            return {"status": "error", "message": f"Connection failed: {exc}"}

    # -------------------------------- sync ---------------------------------
    def sync(self, connector_id: int, config: dict, auth: dict | None = None, *, sync_type: str = "manual") -> ConnectorSyncResult:
        if not self._api_key(config):
            env_var = (config or {}).get("api_key_env") or "GYUTRON_WEBSITE_API_KEY"
            raise GyutronWebsiteAuthError(f"{env_var} is not set in the environment")
        total_found = 0
        total_imported = 0
        notes: list[str] = []
        with self._client(config) as client:
            for data_type, resource in RESOURCES:
                found, imported = self._sync_resource(client, connector_id, data_type, resource)
                total_found += found
                total_imported += imported
                if found:
                    notes.append(f"{resource}:{found}")
        summary = f"Synced {total_imported}/{total_found} records" + (f" ({', '.join(notes)})" if notes else " (no new rows)")
        return ConnectorSyncResult(records_found=total_found, records_imported=total_imported, summary=summary)

    def _sync_resource(self, client: httpx.Client, connector_id: int, data_type: str, resource: str) -> tuple[int, int]:
        state_key = f"since:{resource}"
        since = self._get_state(connector_id, state_key)
        found = 0
        imported = 0
        max_created = since
        cursor: int | None = None
        for _ in range(MAX_PAGES_PER_RESOURCE):
            params: dict = {"limit": PAGE_LIMIT}
            if since:
                params["since"] = since
            if cursor is not None:
                params["cursor"] = cursor
            response = client.get(f"/api/v1/{resource}", params=params)
            if response.status_code in (401, 403):
                raise GyutronWebsiteAuthError(f"API key rejected on {resource} ({response.status_code})")
            if response.status_code == 503:
                raise GyutronWebsiteError(f"Data store unavailable for {resource} (503)")
            response.raise_for_status()
            body = response.json() or {}
            rows = body.get("data") or []
            source = (body.get("meta") or {}).get("source") or "gyutron-website"
            self._register_source(connector_id, source)
            found += len(rows)
            imported += self._upsert_rows(connector_id, source, data_type, rows)
            if data_type == "event":
                self._apply_status_events(connector_id, rows)
                self._normalize_shop_events(rows)
            for row in rows:
                created = row.get("created_at")
                if created and (max_created is None or created > max_created):
                    max_created = created
            cursor = (body.get("pagination") or {}).get("next_cursor")
            if cursor is None:
                break
        if max_created and max_created != since:
            self._set_state(connector_id, state_key, max_created)
        return found, imported

    @staticmethod
    def _upsert_rows(connector_id: int, source: str, data_type: str, rows: list[dict]) -> int:
        if not rows:
            return 0
        count = 0
        with get_connection() as connection:
            for row in rows:
                external_id = row.get("public_id") or row.get("event_id")
                if not external_id:
                    continue
                connection.execute(
                    """
                    INSERT INTO website_data (connector_id, source, data_type, external_id, status, created_at_source, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(connector_id, data_type, external_id) DO UPDATE SET
                      status = excluded.status,
                      data_json = excluded.data_json,
                      synced_at = CURRENT_TIMESTAMP
                    """,
                    (
                        connector_id,
                        source,
                        data_type,
                        external_id,
                        row.get("status"),
                        row.get("created_at"),
                        json.dumps(row, ensure_ascii=False),
                    ),
                )
                count += 1
            connection.commit()
        return count

    _registered_sources: set = set()

    def _register_source(self, connector_id: int, source: str) -> None:
        """Register the API's source identity in data_sources + bind customer
        ownership (idempotent; cached per process)."""
        if source in self._registered_sources:
            return
        from app.services.commerce_store import ensure_source
        from app.services.customers import ensure_customers

        ensure_source(source, source, "website-api", connector_id)
        ensure_customers()
        self._registered_sources.add(source)

    @staticmethod
    def _apply_status_events(connector_id: int, event_rows: list[dict]) -> None:
        """Replay `*.status_changed` events onto the local copies, so a status set in
        the website /admin (e.g. replied/spam) reaches reports & rules without
        re-fetching the row itself (the `since` watermark would skip old rows)."""
        updates = []
        for event in event_rows:
            if not str(event.get("event_type") or "").endswith(".status_changed"):
                continue
            payload = event.get("payload") or {}
            new_status = payload.get("new_status")
            entity_type = event.get("entity_type")
            entity_id = event.get("entity_id")
            if new_status and entity_type and entity_id:
                updates.append((new_status, connector_id, entity_type, entity_id))
        if not updates:
            return
        with get_connection() as connection:
            for new_status, cid, entity_type, entity_id in updates:
                connection.execute(
                    "UPDATE website_data SET status = ?, synced_at = CURRENT_TIMESTAMP WHERE connector_id = ? AND data_type = ? AND external_id = ?",
                    (new_status, cid, entity_type, entity_id),
                )
            connection.commit()

    @staticmethod
    def _normalize_shop_events(event_rows: list[dict]) -> None:
        """Shop BEHAVIOR events (product.viewed / cart.added / quote.requested,
        source=gyutron-shop) also land in the unified commerce `cart_events`
        table. This is a behavior feed, NOT an order connector — anonymous by
        design (no IP / session / PII in the payload)."""
        from app.services.commerce_store import ensure_source, upsert

        shop_events = [
            e for e in event_rows
            if (e.get("source") or "") == "gyutron-shop"
            and (e.get("event_type") or "") in ("product.viewed", "cart.added", "quote.requested")
        ]
        if not shop_events:
            return
        ensure_source("gyutron-shop", "GYUTRON Shop (behavior events)", "shop-events")
        with get_connection() as connection:
            for event in shop_events:
                payload = event.get("payload") or {}
                upsert(
                    connection,
                    "cart_events",
                    "gyutron-shop",
                    event.get("event_id") or "",
                    {
                        "event_type": event.get("event_type"),
                        "product_handle": payload.get("product_handle") or payload.get("product") or None,
                        "locale": payload.get("locale"),
                        "occurred_at": event.get("created_at"),
                    },
                    payload,
                )
            connection.commit()

    # ------------------------------- state ---------------------------------
    @staticmethod
    def _get_state(connector_id: int, key: str) -> str | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT state_value FROM connector_state WHERE connector_id = ? AND state_key = ?",
                (connector_id, key),
            ).fetchone()
        return row["state_value"] if row else None

    @staticmethod
    def _set_state(connector_id: int, key: str, value: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO connector_state (connector_id, state_key, state_value)
                VALUES (?, ?, ?)
                ON CONFLICT(connector_id, state_key) DO UPDATE SET
                  state_value = excluded.state_value,
                  updated_at = CURRENT_TIMESTAMP
                """,
                (connector_id, key, value),
            )
            connection.commit()
