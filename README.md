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

## Demo Flow

1. Open Data Sources.
2. Create a Local Folder connector for `D:\Codex\gyutron-local-business-agent\data\imports`.
3. Put a `.csv`, `.xlsx`, or `.xls` file in that folder.
4. Click Sync.
5. Open Automations.
6. Create Daily Owner Report.
7. Click Run.
8. Open Reports to view the generated local report.
9. Open Overview to see the latest report summary, automation status, sync status, and open alerts.

## Local Data

Runtime data is stored under:

```text
data/
  imports/
  uploads/
  reports/
  db/
    gyutron.sqlite3
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
