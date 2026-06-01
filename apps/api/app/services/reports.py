import json

from app.database import get_connection
from app.services.audit import write_audit_log


def generate_owner_report(source: str = "manual", connector_id: int | None = None, language: str = "en") -> dict:
    with get_connection() as connection:
        uploads = connection.execute(
            "SELECT * FROM uploads ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        rules = connection.execute("SELECT * FROM business_rules WHERE is_active = 1 ORDER BY priority ASC LIMIT 10").fetchall()
        open_alerts = connection.execute("SELECT * FROM alerts WHERE status = 'open' ORDER BY created_at DESC LIMIT 5").fetchall()

        total_files = len(uploads)
        total_size = sum(int(row["file_size"] or 0) for row in uploads)
        is_chinese = language.lower().startswith("zh")
        report_title = "老板日报" if is_chinese else "Owner Daily Report"
        if is_chinese:
            content = f"""# 老板日报

## 老板摘要

GyuTron 已扫描最近 {total_files} 个本地数据文件。导入文件总大小为 {total_size} 字节。本报告基于本地连接器数据、业务规则和提醒状态生成。

## 核心数据变化

- 最近文件：{", ".join(row["original_filename"] for row in uploads[:5]) or "暂无导入文件。"}
- 已参考启用规则：{len(rules)}
- 未处理提醒：{len(open_alerts)}

## 异常提醒

{format_alerts(open_alerts, language)}

## 销售跟进任务

- 复核最新导入的询盘 / 订单文件。
- 检查高优先级国家和逾期未跟进客户。
- 报价前确认库存敏感产品状态。

## 下一步建议

- 保持本地文件夹连接器开启，用于每日导入。
- 每天 09:00 运行老板日报。
- 老板复核后处理未关闭提醒。
"""
        else:
            content = f"""# Owner Daily Report

## Owner Summary

GyuTron scanned {total_files} recent local data file(s). Total imported file size is {total_size} bytes. The report was generated locally from connector data, business rules, and alert status.

## Core Data Changes

- Recent files: {", ".join(row["original_filename"] for row in uploads[:5]) or "No imported files yet."}
- Active rules referenced: {len(rules)}
- Open alerts: {len(open_alerts)}

## Anomaly Alerts

{format_alerts(open_alerts)}

## Sales Follow-up Tasks

- Review newly imported inquiry/order files.
- Check high-priority countries and overdue follow-ups.
- Confirm inventory-sensitive products before sending quotes.

## Next Suggestions

- Keep Local Folder Connector active for daily imports.
- Run this report every morning at 09:00.
- Resolve open alerts after the owner review.
"""
        cursor = connection.execute(
            """
            INSERT INTO reports (
              title, status, content_markdown, summary_json, rules_snapshot_json, model_snapshot_json
            ) VALUES (?, 'ready', ?, ?, ?, ?)
            """,
            (
                report_title,
                content,
                json.dumps({"source": source, "connector_id": connector_id, "files": total_files, "language": language}, ensure_ascii=False),
                json.dumps([dict(row) for row in rules], ensure_ascii=False),
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
        input_summary=f"source={source}, connector_id={connector_id}, language={language}",
        output_summary=f"Owner report generated with {total_files} files.",
    )
    summary = f"已基于 {total_files} 个最近本地文件生成。" if is_chinese else f"Generated from {total_files} recent local file(s)."
    return {"report_id": report_id, "title": report_title, "summary": summary, "language": language}


def format_alerts(alerts, language: str = "en") -> str:
    if not alerts:
        return "- 生成时没有未处理提醒。" if language.lower().startswith("zh") else "- No open alerts at generation time."
    return "\n".join(f"- {row['severity'].upper()}: {row['title']} - {row['description']}" for row in alerts)
