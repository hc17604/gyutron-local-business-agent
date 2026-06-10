"""Website Leads Summary v2 — rules-based (NO AI calls), bilingual.

v2 (Phase 3): built on the shared metrics layer — supports time ranges
(today/7d/30d/all), applies the exclusion rules (spam + internal tests), adds
industry/status aggregations, and emits structured JSON alongside the markdown.
"""
import json
from collections import Counter

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services import website_metrics as metrics
from app.services.rules_engine import report_flags


OVERDUE_HOURS = 48


def generate_website_leads_summary(connector_id: int | None = None, language: str = "en", time_range: str = "all") -> dict:
    zh = (language or "en").lower().startswith("zh")
    if time_range not in metrics.TIME_RANGES:
        time_range = "all"

    if connector_id is None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM data_connectors WHERE connector_type = 'gyutron_website' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        connector_id = row["id"] if row else None

    records = metrics.load_records(connector_id, time_range=time_range)
    totals = metrics.totals_by_type(records)
    rfqs = [i for i in records if i["type"] == "rfq"]
    new_rfqs = [i for i in rfqs if i["status"] == "new"]
    overdue = metrics.overdue_items(records, OVERDUE_HOURS)
    by_country = metrics.count_by(records, "country", types=("rfq",))
    by_category = metrics.count_by(records, "product_category", types=("rfq",))
    by_industry = metrics.count_by(records, "industry", types=("rfq",))
    by_status = Counter(i["status"] for i in rfqs)
    flags = report_flags(connector_id)

    actions_en: list[str] = []
    actions_zh: list[str] = []
    if new_rfqs:
        actions_en.append(f"Quote the {len(new_rfqs)} new RFQ(s) first — RFQs convert best within 24h.")
        actions_zh.append(f"优先报价 {len(new_rfqs)} 条新 RFQ——24 小时内响应转化率最高。")
    if overdue:
        actions_en.append(f"{len(overdue)} item(s) waited over {OVERDUE_HOURS}h — assign an owner today.")
        actions_zh.append(f"{len(overdue)} 条线索等待超过 {OVERDUE_HOURS} 小时——今天指派负责人。")
    if flags["repeat_inquirers"]:
        actions_en.append("Repeat inquirers detected — treat them as high intent.")
        actions_zh.append("发现重复询盘客户——按高意向跟进。")
    if not records:
        actions_en.append("No website data in this range — run a Manual Sync or widen the range.")
        actions_zh.append("该时间范围内没有官网数据——请手动同步或扩大时间范围。")

    range_label = {"today": ("today", "今日"), "yesterday": ("yesterday", "昨日"), "7d": ("last 7 days", "近 7 天"),
                   "30d": ("last 30 days", "近 30 天"), "all": ("all time", "全部")}[time_range]

    def lines(counter, empty):
        return metrics_lines(counter, empty)

    def metrics_lines(counter, empty, limit=8):
        items = counter.most_common(limit)
        return "\n".join(f"- {k}: {v}" for k, v in items) if items else f"- {empty}"

    def overdue_lines(empty):
        if not overdue:
            return f"- {empty}"
        return "\n".join(
            f"- {i['id']} ({i['type']}, {i['status']}) — {i['data'].get('company') or i['data'].get('email') or '?'}, {i['waiting_hours']:.0f}h"
            for i in overdue[:10]
        )

    if zh:
        title = f"官网线索摘要（{range_label[1]}）"
        content = f"""# 官网线索摘要（{range_label[1]}）

## 总览

- 询盘：{totals.get("lead", 0)} · RFQ：{totals.get("rfq", 0)}（新 {len(new_rfqs)}）
- 支持请求：{totals.get("support_request", 0)} · 资料申请：{totals.get("download_request", 0)}

## RFQ 按国家

{lines(by_country, "暂无")}

## RFQ 按品类

{lines(by_category, "暂无")}

## RFQ 按行业

{lines(by_industry, "暂无")}

## RFQ 状态

{metrics_lines(by_status, "暂无")}

## 超时未跟进（>{OVERDUE_HOURS}h）

{overdue_lines("没有超时项。")}

## 建议动作

{chr(10).join(f"- {a}" for a in actions_zh)}
"""
        summary = f"{range_label[1]}：{totals.get('lead',0)} 询盘 / {totals.get('rfq',0)} RFQ（{len(new_rfqs)} 新）/ 超时 {len(overdue)} 条。"
    else:
        title = f"Website Leads Summary ({range_label[0]})"
        content = f"""# Website Leads Summary ({range_label[0]})

## Totals

- Inquiries: {totals.get("lead", 0)} · RFQs: {totals.get("rfq", 0)} ({len(new_rfqs)} new)
- Support: {totals.get("support_request", 0)} · Downloads: {totals.get("download_request", 0)}

## RFQs by country

{lines(by_country, "No data")}

## RFQs by category

{lines(by_category, "No data")}

## RFQs by industry

{lines(by_industry, "No data")}

## RFQ status

{metrics_lines(by_status, "No data")}

## Overdue follow-ups (>{OVERDUE_HOURS}h)

{overdue_lines("Nothing overdue.")}

## Suggested actions

{chr(10).join(f"- {a}" for a in actions_en)}
"""
        summary = f"{range_label[0]}: {totals.get('lead',0)} inquiries / {totals.get('rfq',0)} RFQs ({len(new_rfqs)} new) / {len(overdue)} overdue."

    structured = {
        "report_type": "website_leads_summary", "version": 2, "language": language,
        "time_range": time_range, "connector_id": connector_id,
        "totals": totals, "new_rfqs": len(new_rfqs), "overdue": len(overdue),
        "rfq_by_country": dict(by_country), "rfq_by_category": dict(by_category),
        "rfq_by_industry": dict(by_industry), "rfq_by_status": dict(by_status),
        "flags": flags,
        "recommended_actions": actions_zh if zh else actions_en,
    }
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reports (title, status, content_markdown, summary_json, rules_snapshot_json, model_snapshot_json)
            VALUES (?, 'ready', ?, ?, '[]', ?)
            """,
            (title, content, json.dumps(structured, ensure_ascii=False), json.dumps({"mode": "local_deterministic"})),
        )
        report_id = cursor.lastrowid
        connection.commit()

    write_audit_log("report_generated", "report", target_id=str(report_id), risk_level="low",
                    input_summary=f"website_leads_summary v2 range={time_range} language={language}", output_summary=summary[:200])
    return {"report_id": report_id, "title": title, "summary": summary, "language": language, "structured": structured}
