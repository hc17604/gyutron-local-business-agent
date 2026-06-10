# Commerce Data Model v1 + Connector Spec (Phase 4)

> One unified, source-agnostic commerce model. Every source (website API, shop
> behavior events, CSV imports, future SaaS) writes through the SAME store and
> is consumed by the SAME metrics/rules/tasks/reports layers. Shopify schema is
> the reference frame so a future migration is painless.

## Tables (apps/api/app/database.py)

`orders · order_items · customers · commerce_products · payments · shipments ·
cart_events` (+ `refunds`, `inventory_snapshots` schema-only placeholders).

Invariants on EVERY table:
- `(source, external_id)` composite UNIQUE — idempotent upserts, no duplicates.
- `raw_payload` — SANITIZED original row (replayable on model upgrades).
- `schema_version`, `synced_at`, UTC source timestamps.
- Money triple: `amount` + `currency` + `amount_base` (base = USD, static FX
  table in `commerce_store.FX_TO_BASE`, configurable later).
- Canonical `status` + `raw_status` preserved; maps are CONFIG
  (`ORDER_STATUS_MAP` / `PAYMENT_STATUS_MAP` in `services/commerce_store.py`).

`data_sources` registry: every source registers (source_key, display_name,
kind, connector_id). Report/dashboard source filters key off THIS table.

## Privacy hard rules (services/commerce_sanitize.py)

raw_payload NEVER stores: card numbers (pattern-masked even inside free text),
payment credentials/tokens/secrets, street address lines, phone/fax, tax ids,
waybill/label URLs. Normalized columns carry only what reports need (country,
email for customer merge, amounts, statuses). Behavior events are anonymous:
no IP, no session, no fingerprint. GDPR: `delete_entity(source, external_id)`
cascades across all commerce tables.

## Double-count prevention

Revenue = ORDERS in paid/fulfilled state only. `payments.order_ref` exists for
RECONCILIATION (`revenue_reconciliation()`), never summed as revenue alongside
orders. Customer merge across sources happens at the VIEW layer by email;
per-source rows are kept intact.

## Adapter contract (= BaseConnector, proven by 3 implementations)

```
manifest()                          -> identity/auth_type/status
test_connection(config, auth)      -> {status, message}
sync(connector_id, config, auth)   -> ConnectorSyncResult  (incremental via own watermark/state)
```
Writers MUST go through `commerce_store.upsert` / `ensure_source` — that is
where sanitization + idempotency + registration are enforced.

Implementations: `gyutron_website` (HTTPS Data API), `csv_commerce`
(mapping-driven CSV), shop behavior events (normalized from the website event
stream — a BEHAVIOR feed, not an order connector).

## CSV mappings (connectors/csv_mappings.py — config only, zero importer code)

Per file kind: `external_id` rule, column map with `type` coercion
(str/int/float/date — multi-format date parsing, currency symbol stripping),
`required` flags, `status_map` hook. Shipped: `generic` + `shopify`.
New platform/customer = new mapping dict + a connector row with
`{source_key, folder_path, mapping}` — no core changes (ACME Industrial mock
in `samples/acme-industrial/` is the living proof).

## What a 3rd party must provide to plug in (connector spec)

EITHER a read-only HTTPS API shaped like the GYUTRON Data API contract
(`{data, pagination, meta}` envelope, Bearer key, `since`/`cursor`/`limit`) —
the gyutron_website connector then works with a different base URL/key;
OR CSV exports of orders / order_items / customers / payments with any column
names (a mapping config adapts them). Minimum fields: external id, status,
amount+currency, created_at; email/country strongly recommended.

## Future SaaS connector design (paper only — Phase 4 rule: no code for unused platforms)

- **Shopify**: REST/GraphQL Admin API → orders/customers/products map 1:1 onto
  this model (the canonical status maps already use Shopify vocabulary);
  `updated_at_min` = the `since` watermark.
- **Stripe**: charges/payment_intents → `payments` (order_ref = metadata
  order id); products/prices → `commerce_products`.
- Both follow the same adapter contract; secrets via env, never config_json.
