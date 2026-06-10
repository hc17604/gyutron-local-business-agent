"""Website Leads Summary — rules-based (NO AI calls), bilingual.

Aggregates the rows synced by the GYUTRON Website connector (`website_data`)
into a boss-readable markdown report: totals, new RFQs, country / product
breakdowns, overdue follow-ups, and suggested next actions. Stored in the
`reports` table like the owner daily report.
"""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.database import get_connection
from app.services.audit import write_audit_log


OVERDUE_HOURS = 48
FOLLOWUP_TYPES = ("lead", "rfq", "support_request")
OPEN_STATUSES = ("new", "reviewing")


def _parse_created(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def generate_website_leads_summary(connector_id: int | None = None, language: str = "en") -> dict:
    is_chinese = (language or "en").lower().startswith("zh")

    with get_connection() as connection:
        if connector_id is None:
            row = connection.execute(
                "SELECT id FROM data_connectors WHERE connector_type = 'gyutron_website' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            connector_id = row["id"] if row else None
        rows = connection.execute(
            "SELECT data_type, external_id, status, created_at_source, data_json FROM website_data WHERE connector_id IS ?"
            if connector_id is None
            else "SELECT data_type, external_id, status, created_at_source, data_json FROM website_data WHERE connector_id = ?",
            (connector_id,),
        ).fetchall()

    parsed = []
    for row in rows:
        try:
            data = json.loads(row["data_json"] or "{}")
        except json.JSONDecodeError:
            data = {}
        parsed.append({"type": row["data_type"], "id": row["external_id"], "status": row["status"], "created": row["created_at_source"], "data": data})

    totals = Counter(item["type"] for item in parsed)
    rfqs = [item for item in parsed if item["type"] == "rfq"]
    new_rfqs = [item for item in rfqs if item["status"] == "new"]
    support = [item for item in parsed if item["type"] == "support_request"]
    downloads = [item for item in parsed if item["type"] == "download_request"]
    leads = [item for item in parsed if item["type"] == "lead"]

    rfq_by_country = Counter((item["data"].get("country") or "—") for item in rfqs)
    rfq_by_category = Counter((item["data"].get("product_category") or "—") for item in rfqs)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=OVERDUE_HOURS)
    overdue = []
    for item in parsed:
        if item["type"] not in FOLLOWUP_TYPES or item["status"] not in OPEN_STATUSES:
            continue
        created = _parse_created(item["created"])
        if created and created < cutoff:
            overdue.append(item)

    def fmt_counter(counter: Counter, empty: str) -> str:
        if not counter:
            return f"- {empty}"
        return "\n".join(f"- {key}: {count}" for key, count in counter.most_common(8))

    def fmt_overdue(empty: str) -> str:
        if not overdue:
            return f"- {empty}"
        lines = []
        for item in overdue[:10]:
            who = item["data"].get("company") or item["data"].get("email") or "?"
            lines.append(f"- {item['id']} ({item['type']}, {item['status']}) — {who}, {item['created'] or '?'}")
        return "\n".join(lines)

    # Suggested actions are simple deterministic rules — no model calls.
    actions_en: list[str] = []
    actions_zh: list[str] = []
    if new_rfqs:
        actions_en.append(f"Quote the {len(new_rfqs)} new RFQ(s) first — RFQs convert best within 24h.")
        actions_zh.append(f"优先报价 {len(new_rfqs)} 条新 RFQ——24 小时内响应转化率最高。")
    if overdue:
        actions_en.append(f"{len(overdue)} item(s) have sat in new/reviewing for over {OVERDUE_HOURS}h — assign an owner today.")
        actions_zh.append(f"{len(overdue)} 条线索停留在 new/reviewing 超过 {OVERDUE_HOURS} 小时——今天指派负责人。")
    if support and len([s for s in support if s["status"] == "new"]):
        actions_en.append("Answer open support requests before they age — support speed drives reorder behavior.")
        actions_zh.append("尽快回复未处理的支持请求——售后响应速度直接影响复购。")
    if downloads:
        actions_en.append("Fulfil approved download requests and follow up — datasheet requesters are active evaluators.")
        actions_zh.append("尽快交付已批准的资料请求并跟进——索取资料的客户正处于选型阶段。")
    if not parsed:
        actions_en.append("No website data synced yet — run a Manual Sync on the GYUTRON Website connector.")
        actions_zh.append("尚未同步到官网数据——请先在 GYUTRON 官网连接器上执行手动同步。")

    top_country = rfq_by_country.most_common(1)[0][0] if rfq_by_country else None

    if is_chinese:
        title = "官网线索摘要"
        content = f"""# 官网线索摘要

## 总览

- 官网询盘（Contact/Leads）：{totals.get("lead", 0)}
- 报价请求（RFQ）：{totals.get("rfq", 0)}（其中新进 {len(new_rfqs)} 条）
- 支持请求：{totals.get("support_request", 0)}
- 资料下载申请：{totals.get("download_request", 0)}
- 事件流记录：{totals.get("event", 0)}

## RFQ 按国家/地区

{fmt_counter(rfq_by_country, "暂无 RFQ 数据。")}

## RFQ 按产品类别

{fmt_counter(rfq_by_category, "暂无 RFQ 数据。")}

## 超时未跟进（>{OVERDUE_HOURS} 小时仍为 new/reviewing）

{fmt_overdue("没有超时未跟进项。")}

## 建议动作

{chr(10).join(f"- {a}" for a in actions_zh)}
"""
        summary = f"官网数据：{totals.get('lead',0)} 询盘 / {totals.get('rfq',0)} RFQ（{len(new_rfqs)} 新）/ {totals.get('support_request',0)} 支持 / {totals.get('download_request',0)} 资料申请；超时未跟进 {len(overdue)} 条。"
        if top_country and top_country != "—":
            summary += f" RFQ 最多来自 {top_country}。"
    else:
        title = "Website Leads Summary"
        content = f"""# Website Leads Summary

## Totals

- Website inquiries (contact/leads): {totals.get("lead", 0)}
- Quote requests (RFQ): {totals.get("rfq", 0)} ({len(new_rfqs)} new)
- Support requests: {totals.get("support_request", 0)}
- Download requests: {totals.get("download_request", 0)}
- Event-stream records: {totals.get("event", 0)}

## RFQs by country / region

{fmt_counter(rfq_by_country, "No RFQ data yet.")}

## RFQs by product category

{fmt_counter(rfq_by_category, "No RFQ data yet.")}

## Overdue follow-ups (new/reviewing for >{OVERDUE_HOURS}h)

{fmt_overdue("Nothing overdue.")}

## Suggested actions

{chr(10).join(f"- {a}" for a in actions_en)}
"""
        summary = f"Website data: {totals.get('lead',0)} inquiries / {totals.get('rfq',0)} RFQs ({len(new_rfqs)} new) / {totals.get('support_request',0)} support / {totals.get('download_request',0)} downloads; {len(overdue)} overdue follow-up(s)."
        if top_country and top_country != "—":
            summary += f" Most RFQs from {top_country}."

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reports (title, status, content_markdown, summary_json, rules_snapshot_json, model_snapshot_json)
            VALUES (?, 'ready', ?, ?, ?, ?)
            """,
            (
                title,
                content,
                json.dumps(
                    {
                        "source": "gyutron_website",
                        "connector_id": connector_id,
                        "language": language,
                        "totals": dict(totals),
                        "new_rfqs": len(new_rfqs),
                        "overdue": len(overdue),
                        "rfq_by_country": dict(rfq_by_country),
                        "rfq_by_category": dict(rfq_by_category),
                    },
                    ensure_ascii=False,
                ),
                json.dumps([], ensure_ascii=False),
                json.dumps({"mode": "local_deterministic"}, ensure_ascii=False),
            ),
        )
        report_id = cursor.lastrowid
        connection.commit()

    write_audit_log(
        "report_generated",
        "report",
        target_id=str(report_id),
        risk_level="low",
        input_summary=f"website_leads_summary connector_id={connector_id} language={language}",
        output_summary=summary[:200],
    )
    return {"report_id": report_id, "title": title, "summary": summary, "language": language}
