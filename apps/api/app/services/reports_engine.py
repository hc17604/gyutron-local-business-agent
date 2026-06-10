"""Reports Engine v1 — deterministic, bilingual report generators.

Daily Owner Report / Weekly Pipeline Report / Opportunities. All numbers come
from the local `website_data` store via the metrics layer (exclusions applied);
recommendations come from the rules engine. No model calls — reports must be
fully usable with zero AI configured.
"""
import json
from collections import Counter

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services import website_metrics as metrics
from app.services.rules_engine import report_flags


def _store_report(title: str, content: str, summary_json: dict) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reports (title, status, content_markdown, summary_json, rules_snapshot_json, model_snapshot_json)
            VALUES (?, 'ready', ?, ?, '[]', ?)
            """,
            (title, content, json.dumps(summary_json, ensure_ascii=False), json.dumps({"mode": "local_deterministic"})),
        )
        report_id = cursor.lastrowid
        connection.commit()
    write_audit_log("report_generated", "report", target_id=str(report_id), risk_level="low",
                    input_summary=summary_json.get("report_type", "report"), output_summary=title)
    return report_id


def _open_tasks(limit: int = 10) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, priority, rule_id, entity_id FROM agent_tasks WHERE status = 'open' "
            "ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _counter_lines(counter, empty: str, limit: int = 8) -> str:
    items = counter.most_common(limit) if isinstance(counter, Counter) else sorted(counter.items(), key=lambda x: -x[1])[:limit]
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {k}: {v}" for k, v in items)


def _delta(a: int, b: int) -> str:
    diff = a - b
    return f"+{diff}" if diff > 0 else (str(diff) if diff < 0 else "±0")


TYPE_LABELS = {
    "en": {"lead": "Inquiries", "rfq": "RFQs", "support_request": "Support", "download_request": "Downloads"},
    "zh": {"lead": "询盘", "rfq": "RFQ", "support_request": "支持请求", "download_request": "资料申请"},
}


# ------------------------------ Daily Owner Report --------------------------- #
def generate_daily_owner_report(language: str = "en", connector_id: int | None = None) -> dict:
    zh = (language or "en").lower().startswith("zh")
    L = TYPE_LABELS["zh" if zh else "en"]

    yesterday = metrics.load_records(connector_id, time_range="yesterday")
    today = metrics.load_records(connector_id, time_range="today")
    all_records = metrics.load_records(connector_id)
    y_tot, t_tot = metrics.totals_by_type(yesterday), metrics.totals_by_type(today)

    # day-before for the ± comparison
    import datetime as _dt
    db_start, db_end = metrics.range_bounds("yesterday")
    day_before = []
    if db_start:
        for item in all_records:
            if item["created"] and (db_start - _dt.timedelta(days=1)) <= item["created"] < db_start:
                day_before.append(item)
    d_tot = metrics.totals_by_type(day_before)

    open_now = metrics.open_items(all_records)
    oldest_wait = max((metrics.waiting_hours(i) or 0 for i in open_now), default=0)
    overdue = metrics.overdue_items(all_records, 24)
    flags = report_flags(connector_id)
    tasks = _open_tasks()
    rfq_recent = metrics.load_records(connector_id, time_range="7d")

    def block_counts(tot: dict, ref: dict) -> str:
        return "\n".join(
            f"- {L[t]}: {tot.get(t, 0)} ({_delta(tot.get(t, 0), ref.get(t, 0))})"
            for t in ("lead", "rfq", "support_request", "download_request")
        )

    def overdue_lines(empty: str) -> str:
        if not overdue:
            return f"- {empty}"
        return "\n".join(
            f"- {i['id']} ({L[i['type']]}, {i['status']}) — {i['data'].get('company') or i['data'].get('email') or '?'},"
            f" {i['waiting_hours']:.0f}h" for i in overdue[:10]
        )

    def task_lines(empty: str) -> str:
        if not tasks:
            return f"- {empty}"
        return "\n".join(f"- [{t['priority']}] {t['title']} (rule: {t['rule_id']})" for t in tasks)

    def flag_lines() -> list[str]:
        out = []
        for s in flags["surge_days"]:
            out.append(("RFQ 爆量：" if zh else "RFQ surge: ") + f"{s['day']} × {s['count']}")
        for r in flags["repeat_inquirers"]:
            out.append(("高意向（多次询盘）：" if zh else "High intent (repeat inquirer): ") + f"{r['email']} × {r['count']}")
        return out

    risks = flag_lines()
    risk_block = "\n".join(f"- {r}" for r in risks) if risks else ("- 无" if zh else "- None")

    if zh:
        title = "老板日报"
        content = f"""# 老板日报

## 昨日新增（对比前一日）

{block_counts(y_tot, d_tot)}

## 今日截至目前

{block_counts(t_tot, y_tot)}

## 未处理（status=new/reviewing）

- 总量：{len(open_now)}（最久等待 {oldest_wait:.0f} 小时）

## 超时未跟进（>24 小时）

{overdue_lines("没有超时项。")}

## RFQ 分布（近 7 天）

按国家：
{_counter_lines(metrics.count_by(rfq_recent, "country", types=("rfq",)), "暂无")}

按产品品类：
{_counter_lines(metrics.count_by(rfq_recent, "product_category", types=("rfq",)), "暂无")}

## 风险与机会预警

{risk_block}

## 待办任务（open）

{task_lines("暂无任务。")}
"""
        summary = f"昨日新增 {sum(y_tot.values())} 条；未处理 {len(open_now)} 条；超时 {len(overdue)} 条；open 任务 {len(tasks)} 个。"
    else:
        title = "Daily Owner Report"
        content = f"""# Daily Owner Report

## Yesterday (vs the day before)

{block_counts(y_tot, d_tot)}

## Today so far

{block_counts(t_tot, y_tot)}

## Unprocessed (status new/reviewing)

- Total: {len(open_now)} (oldest waiting {oldest_wait:.0f}h)

## Overdue follow-ups (>24h)

{overdue_lines("Nothing overdue.")}

## RFQ distribution (last 7 days)

By country:
{_counter_lines(metrics.count_by(rfq_recent, "country", types=("rfq",)), "No data")}

By product category:
{_counter_lines(metrics.count_by(rfq_recent, "product_category", types=("rfq",)), "No data")}

## Risk & opportunity flags

{risk_block}

## Open tasks

{task_lines("No open tasks.")}
"""
        summary = f"Yesterday: {sum(y_tot.values())} new; {len(open_now)} unprocessed; {len(overdue)} overdue; {len(tasks)} open task(s)."

    report_id = _store_report(title, content, {
        "report_type": "daily_owner", "language": language, "connector_id": connector_id,
        "yesterday": y_tot, "today": t_tot, "unprocessed": len(open_now), "overdue": len(overdue),
        "open_tasks": len(tasks), "flags": flags,
    })
    return {"report_id": report_id, "title": title, "summary": summary, "language": language}


# ---------------------------- Weekly Pipeline Report -------------------------- #
def generate_weekly_pipeline_report(language: str = "en", connector_id: int | None = None) -> dict:
    zh = (language or "en").lower().startswith("zh")
    L = TYPE_LABELS["zh" if zh else "en"]
    week = metrics.load_records(connector_id, time_range="7d")
    all_records = metrics.load_records(connector_id)
    totals = metrics.totals_by_type(week)
    funnel = metrics.rfq_funnel(all_records)
    open_now = metrics.open_items(all_records)
    trend = metrics.day_counts(week, days=7)
    tasks = _open_tasks()

    trend_lines = "\n".join(f"- {day}: {n}" for day, n in trend)
    funnel_line = " → ".join(f"{k} {v}" for k, v in funnel.items())

    def dist(field, types):
        return _counter_lines(metrics.count_by(week, field, types=types), "—")

    if zh:
        title = "周报（管道）"
        content = f"""# 周报（管道）

## 本周总量（近 7 天）

{chr(10).join(f"- {L[t]}: {totals.get(t, 0)}" for t in ("lead", "rfq", "support_request", "download_request"))}

## 7 日趋势（全部提交）

{trend_lines}

## RFQ 漏斗（全量）

- {funnel_line}

## 分布（近 7 天）

RFQ 按国家：
{dist("country", ("rfq",))}

RFQ 按品类：
{dist("product_category", ("rfq",))}

RFQ 按行业：
{dist("industry", ("rfq",))}

支持请求按类型：
{dist("issue_type", ("support_request",))}

资料申请按文件：
{dist("requested_file", ("download_request",))}

## 未关闭事项

- 共 {len(open_now)} 条仍为 new/reviewing；open 任务 {len(tasks)} 个

## 下周建议

- 清零超时未跟进项，优先重点国家/品类 RFQ
- 复盘出现多次信号的品类（见机会报告）
"""
        summary = f"本周 {sum(totals.values())} 条提交；漏斗 {funnel_line}；未关闭 {len(open_now)} 条。"
    else:
        title = "Weekly Pipeline Report"
        content = f"""# Weekly Pipeline Report

## This week (last 7 days)

{chr(10).join(f"- {L[t]}: {totals.get(t, 0)}" for t in ("lead", "rfq", "support_request", "download_request"))}

## 7-day trend (all submissions)

{trend_lines}

## RFQ funnel (all time)

- {funnel_line}

## Distributions (last 7 days)

RFQs by country:
{dist("country", ("rfq",))}

RFQs by category:
{dist("product_category", ("rfq",))}

RFQs by industry:
{dist("industry", ("rfq",))}

Support by issue type:
{dist("issue_type", ("support_request",))}

Downloads by file:
{dist("requested_file", ("download_request",))}

## Open items

- {len(open_now)} still new/reviewing; {len(tasks)} open task(s)

## Suggested next week

- Clear overdue follow-ups first; prioritise priority-market RFQs
- Review categories with repeated signals (see the Opportunities report)
"""
        summary = f"{sum(totals.values())} submissions this week; funnel {funnel_line}; {len(open_now)} open."

    report_id = _store_report(title, content, {
        "report_type": "weekly_pipeline", "language": language, "connector_id": connector_id,
        "totals": totals, "funnel": funnel, "open": len(open_now),
    })
    return {"report_id": report_id, "title": title, "summary": summary, "language": language}


# ------------------------------ Opportunities -------------------------------- #
def generate_opportunities_report(language: str = "en", connector_id: int | None = None) -> dict:
    zh = (language or "en").lower().startswith("zh")
    month = metrics.load_records(connector_id, time_range="30d")
    matrix = metrics.category_country_matrix(month)
    events = metrics.event_type_counts(connector_id)
    pages = metrics.count_by(month, "source_page")
    utm = metrics.count_by(month, "utm_source", empty_label="(direct)")

    matrix_lines = []
    for cat, countries in sorted(matrix.items(), key=lambda x: -sum(x[1].values())):
        pairs = ", ".join(f"{c}×{n}" for c, n in sorted(countries.items(), key=lambda x: -x[1]))
        matrix_lines.append(f"- {cat}: {pairs}")
    matrix_block = "\n".join(matrix_lines) if matrix_lines else ("- 暂无 RFQ 数据" if zh else "- No RFQ data yet")

    if zh:
        title = "机会分析（30 天）"
        content = f"""# 机会分析（30 天）

## 品类 × 国家 RFQ 矩阵

{matrix_block}

## 事件类型分布（全量）

{_counter_lines(Counter(events), "暂无事件")}

## 来源页 Top

{_counter_lines(pages, "暂无")}

## UTM 渠道

{_counter_lines(utm, "暂无")}
"""
        summary = f"30 天内 {len(matrix)} 个品类出现 RFQ 信号。"
    else:
        title = "Opportunities (30 days)"
        content = f"""# Opportunities (30 days)

## Category × country RFQ matrix

{matrix_block}

## Event type distribution (all time)

{_counter_lines(Counter(events), "No events")}

## Top source pages

{_counter_lines(pages, "No data")}

## UTM channels

{_counter_lines(utm, "No data")}
"""
        summary = f"{len(matrix)} categories show RFQ signals in the last 30 days."

    report_id = _store_report(title, content, {
        "report_type": "opportunities", "language": language, "connector_id": connector_id,
        "matrix": matrix, "events": events,
    })
    return {"report_id": report_id, "title": title, "summary": summary, "language": language}
