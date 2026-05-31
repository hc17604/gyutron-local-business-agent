# GyuTron Local Agent API

This document tracks the local-first API surface for the MVP. All endpoints run on the customer machine or local server. API keys, uploaded files, reports, rules, field mappings, chat history, patch proposals, and audit logs are stored locally in SQLite unless explicitly changed by deployment configuration.

## Health

### `GET /health`

Returns backend status and local storage paths.

## Model Settings

### `GET /settings/model`

Returns the active model configuration with the API key masked.

### `POST /settings/model`

Saves the active model configuration locally.

Supported providers:
- `openai_compatible`
- `openai`
- `deepseek`
- `custom`
- `ollama`
- `lm_studio`

### `POST /settings/model/test`

Tests the configured model with:

```text
Reply only with OK.
```

The backend calls:

```text
POST {base_url}/chat/completions
```

### `GET /settings/model/providers`

Returns provider metadata and default local endpoints.

## Agent Chat

### `POST /agent/chat`

Sends a real chat message to the configured model.

Modes:
- `business`
- `engineering`
- `mixed`

The request can include selected project files. Only files inside the workspace root and outside ignored/sensitive paths are readable.

### `GET /agent/conversations`

Lists recent local conversations.

### `GET /agent/conversations/{conversation_id}/messages`

Lists messages for one conversation.

## Workspace

### `GET /workspace/tree`

Returns a filtered project file tree.

### `GET /workspace/file?path=...`

Reads a single safe text file from the workspace.

### `POST /workspace/search`

Searches project files by filename/path/content with extension and result limits.

### `POST /workspace/context`

Returns selected safe file contents for Agent context.

Security rules:
- Workspace root defaults to the repository root.
- Override with `GYUTRON_WORKSPACE_ROOT`.
- Files outside workspace root are blocked.
- `.env`, `.env.*`, `.git`, `node_modules`, `dist`, `build`, `__pycache__`, `data/db`, and `data/uploads` are blocked.
- Single file read limit is 200 KB.
- Context file count limit is 20.

## Engineering Agent

### `POST /agent/engineering/plan`

Returns an engineering plan before patch generation.

### `POST /agent/engineering/propose-patch`

Uses the configured model to generate a patch proposal from selected files. It stores the proposal locally and returns a diff preview.

### `POST /agent/engineering/apply-patch`

Applies a proposal only when `confirmed=true`. The backend saves before/after content and an audit log.

### `GET /agent/engineering/changes`

Lists recent file changes.

### `POST /agent/engineering/rollback`

Restores a file from the saved `before_content` only when `confirmed=true`.

## Audit

The backend writes audit logs for:
- model connection tests
- Agent Chat messages
- workspace tree/file/search/context reads
- engineering plans
- patch proposals
- patch application
- rollback
- connector create/test/sync
- automation create/update/run/pause/resume/delete
- alert create/update/acknowledge/resolve

## Connectors

### `GET /connectors/catalog`

Returns available connector plugins. Real MVP connectors:
- `excel_csv`
- `local_folder`

Mock placeholders:
- `alibaba`
- `shopee`
- `amazon`
- `shopify`

### `GET /connectors`

Lists configured local data connectors and connector catalog metadata.

### `POST /connectors`

Creates a connector record.

Example local folder config:

```json
{
  "connector_type": "local_folder",
  "name": "Local imports",
  "config_json": {
    "folder_path": "D:\\Codex\\gyutron-local-business-agent\\data\\imports",
    "data_type": "order"
  }
}
```

### `POST /connectors/{connector_id}/test`

Tests connector configuration without external side effects.

### `POST /connectors/{connector_id}/sync`

Runs a manual sync. Local Folder sync scans `.csv`, `.xlsx`, and `.xls` files, imports new files into local upload records, and creates a `SyncJob`.

### `GET /connectors/{connector_id}/sync-jobs`

Lists sync history.

### `POST /connectors/local-folder/scan`

Convenience endpoint for scanning the latest configured local folder connector.

## Automations

### `GET /automations`

Lists local automation rules.

### `POST /automations`

Creates an automation rule. Supported triggers:
- `manual`
- `schedule`
- `data_updated`

Supported MVP actions:
- `generate_report`
- `scan_connector`
- `create_alert`
- `run_agent_analysis` placeholder

Schedule format for MVP:
- `daily:09:00`
- `weekly:mon:09:00`

### `POST /automations/{id}/run`

Runs an automation manually and creates an `AutomationRun`.

### `POST /automations/{id}/pause`

Pauses an active automation.

### `POST /automations/{id}/resume`

Resumes a paused automation and recalculates `next_run_at`.

### `GET /automations/{id}/runs`

Lists automation run history.

## Reports

### `GET /reports`

Lists local reports.

### `POST /reports/generate-owner-report`

Generates a deterministic local owner report from recent uploads, active business rules, and open alerts. This first version does not send email or push to external systems.

## Alerts

### `GET /alerts`

Lists local alerts.

### `POST /alerts`

Creates an alert.

### `POST /alerts/{id}/acknowledge`

Marks an alert as acknowledged.

### `POST /alerts/{id}/resolve`

Marks an alert as resolved.

## Overview

### `GET /overview`

Returns the latest report summary, active automations, recent sync jobs, and open alerts for the dashboard.
