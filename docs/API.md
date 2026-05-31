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
