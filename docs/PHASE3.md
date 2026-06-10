# Phase 3 — Reports, Tasks & Business Rules

> Goal: upgrade the Agent Workspace from "can read website data" to "drives
> business action". Everything is rules/statistics based — fully usable with NO
> AI model configured. Bilingual (en / zh-CN) throughout.

## Data flow

```
gyutron.com forms → D1 → events (incl. *.status_changed from /admin)
        ↓  GET /api/v1/*  (Bearer key, read-only — never the database)
gyutron_website connector  (manual sync OR "Website auto-sync" every 15 min)
        ↓  upsert into website_data  (+ status_changed replay onto local rows)
rules engine (auto after every sync)  →  agent_tasks (idempotent) + rule_triggers
        ↓
reports engine  →  reports table  →  Reports UI / "Daily owner report" 08:00
```

Pages render from the LOCAL store — no live API calls per page view.

## Modules (apps/api/app/…)

| Module | Purpose |
|---|---|
| `services/website_metrics.py` | THE metric foundation: loads `website_data`, applies exclusions (spam + internal-test markers), time ranges (today/yesterday/7d/30d/all), aggregations, funnel, overdue, day buckets. |
| `services/rules_engine.py` | Business Rules v1: 10 config-driven rules (`RULES`), runtime state in `rule_state` (enabled/config/counters), evaluation → idempotent tasks (UNIQUE rule_id+entity_id) + auto-close when the entity stops matching + `rule_triggers` log. |
| `services/reports_engine.py` | Daily Owner Report / Weekly Pipeline / Opportunities (bilingual, reference open tasks + rule flags). |
| `services/website_leads.py` | Leads Summary **v2**: time_range param, exclusions, country/category/industry/status aggregations, structured JSON + recommended actions. |
| `services/bootstrap.py` | Startup seeds: rule_state rows + the 2 default automations (when a gyutron_website connector exists). |
| `routers/tasks.py` | `GET /tasks` (status/priority/type filters) · `PATCH /tasks/{id}` (done/dismissed) · `POST /tasks/evaluate`. |
| `routers/rules.py` | `GET /business-rules` · `POST /business-rules/{id}/toggle` · `GET /business-rules/{id}/triggers`. |
| `routers/reports.py` | + `POST /reports/daily-owner` · `/weekly-pipeline` · `/opportunities`; `/website-leads-summary` gains `time_range`. |
| `scheduler/runner.py` | + `connector_sync` (sync **and** rules evaluation) and `generate_daily_owner_report` actions. `cron.py` gains `every:N` minutes. |
| connector | Replays `*.status_changed` events onto local rows — a status set in the website /admin (replied/spam) reaches reports & rules without re-fetching old rows. |

## The rules (all configurable via rule_state.config_json, toggleable in the UI)

1. `rfq_followup` — open RFQ → task; >24h waiting OR priority country/category → high.
2. `support_review` — open support request → task; >24h → high.
3. `download_review` — manual_review/gated download not fulfilled → task.
4. `category_opportunity` — ≥3 RFQ/download signals for a category in 7d → review task.
5. `data_hygiene` — lead/RFQ missing email/country → low task.
6. `priority_countries` — MY/VN/SG/TH/ID/DE boost (modifier).
7. `priority_categories` — vision/scanning/PDA/sensing/measurement slugs boost (modifier).
8. `rfq_surge_daily` — ≥3 RFQs in a day → daily-report flag.
9. `repeat_inquirer` — same email ≥2 submissions → high-intent flag.
10. `exclude_internal_tests` — spam status + "GYUTRON Internal Test" company + `e2e-test` utm are excluded from ALL metrics (raw rows kept for audit).

Idempotency: a (rule, entity) pair creates at most one task ever; tasks auto-close
when the entity stops matching (e.g. /admin sets "replied" → event → sync).

## Default automations (seeded at startup, owner-editable, matched by name)

- **Website auto-sync** — `every:15` → `connector_sync` (sync + rules).
- **Daily owner report** — `daily:08:00` → bilingual daily report.

## Trade-offs / deliberate choices

- Rules are code-defined defaults + DB-backed state, NOT a generic rule editor —
  per the brief: no complex engine, no NL parsing, no LLM in the loop.
- Continuous-3-day unattended acceptance is replaced by mechanism verification
  (scheduler `every:N` + manual automation run exercised end-to-end) — the
  scheduler is the same loop that already ran existing automations.
- A re-resolved entity that becomes overdue AGAIN does not currently re-open its
  done task (UNIQUE constraint). Upgrade path: include a status-epoch in the
  dedup key.
- Phase 4 (shop/external connectors): add a connector per source reusing
  `BaseConnector` + `website_data.source` column; metrics already key by source.

## Tests

`tests/test_phase3_engines.py` (+ updated connector tests): exclusion filtering,
idempotent task creation, priority boosting, auto-close loop, rule toggling,
bilingual daily/weekly/opportunities generation, Summary v2 time ranges.
13 passed; `npm run build` + `check:i18n` clean.
