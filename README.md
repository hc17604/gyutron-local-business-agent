# GyuTron Local Agent

GyuTron Local Agent is a local-first business automation agent for cross-border manufacturing, ecommerce, and industrial trade teams.

It is not a SaaS dashboard and not a generic chatbot. Customer data, field mappings, business rules, reports, model settings, connector records, automation history, and audit logs are stored locally by default.

## Current MVP

- FastAPI backend
- React + Vite + TypeScript frontend
- SQLite local database
- Local model configuration for OpenAI-compatible endpoints, OpenAI, DeepSeek, Ollama, LM Studio, and custom endpoints
- Agent Chat with Business / Engineering / Mixed modes
- Safe local workspace file reading
- Engineering patch proposal, diff preview, confirmed apply, and rollback API
- Connector plugin system
- Real MVP connectors: Excel / CSV and Local Folder
- Mock connector placeholders: Alibaba, Shopee, Amazon, Shopify
- Local automation rules and automation run history
- Lightweight local scheduler
- Scheduled Owner Report generation
- Local alerts with acknowledge / resolve
- Overview, Data Sources, Automations, Reports, Agent Chat, Memory, Tasks, Audit Logs, Model Settings, and System Settings pages
- First-run Onboarding Wizard
- Local owner/admin/operator/viewer accounts
- Security Center with data policy and redaction preview
- Backup & Restore
- Local trial/license structure
- Demo data loading for customer presentations

## Local Development

Backend:

```powershell
cd D:\Codex\gyutron-local-business-agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
cd apps\api
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd D:\Codex\gyutron-local-business-agent\apps\web
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open:

- Web: http://127.0.0.1:5173
- API health: http://127.0.0.1:8000/health

## Docker Deployment

Copy `.env.example` to `.env`, adjust ports and paths, then run:

```powershell
.\scripts\start.ps1
```

or on Linux/macOS:

```bash
scripts/start.sh
```

Default Docker URLs:

- Web: http://localhost:3000
- API: http://localhost:8000

Docker mounts `./data` into the API container, so SQLite, reports, backups, and runtime data persist after container restarts.

## Demo Flow

1. Open the web app for the first time.
2. Complete Onboarding.
3. Create the local owner account.
4. Skip model setup or configure an OpenAI-compatible endpoint.
5. Load Demo Data.
6. Enter Overview.
7. Generate an Owner Report.
8. Open Audit Logs.
9. Create a backup in Backup & Restore.
10. Open Data Sources, create a Local Folder connector, and sync `.csv`, `.xlsx`, or `.xls` files.

## UI Preview Notes

The current interface is designed as a restrained enterprise desktop console:

- AppShell with dark local-first sidebar and compact operations header.
- Agent Chat as a command center, with mode switching, command chips, structured messages, tool metadata, loading, and error states.
- Data Sources as a connector management center.
- Reports as readable owner-report sections instead of raw Markdown.
- Model Settings with provider cards and local model guidance.
- Audit Logs with a real local audit trail and empty state.

The visual system uses shared tokens in `apps/web/src/styles/globals.css` for colors, spacing, radius, shadows, buttons, badges, cards, tables, and form controls.

## Local Data

Runtime data is stored under:

```text
data/
  imports/
  uploads/
  reports/
  db/
    gyutron.sqlite3
  backups/
```

`data/` is ignored by Git. Do not place customer data, generated databases, API keys, reports, or uploads on the C drive.

## Safety Rules

- No hardcoded API keys.
- API keys and connector auth are not printed in logs.
- Customer data is not uploaded to a GyuTron cloud service by default.
- Platform connectors are placeholders until explicitly implemented.
- The first version is read-first.
- No automatic email sending.
- No automatic platform data modification.
- No arbitrary shell execution by the Agent.
- Medium and high-risk actions require explicit confirmation.

## Local Roles

- `owner`: full local control, backup/restore, users, model settings, patch apply.
- `admin`: model settings, connectors, automations, audit logs.
- `operator`: upload/sync data, generate reports, view dashboards.
- `viewer`: read-only business views.

## Backup And Restore

Use the UI page `Backup & Restore` or:

```bash
scripts/backup.sh
scripts/restore.sh data/backups/<backup-file>.zip
```

Uploads are excluded from API-created backups by default. Restore is owner-only and creates a pre-restore snapshot.

## License Trial

The MVP starts in local `trial` mode for 14 days. License activation is local-only for now and does not contact a remote payment or license server.
