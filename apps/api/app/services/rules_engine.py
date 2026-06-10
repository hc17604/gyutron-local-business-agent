"""Business Rules v1 — a minimal, config-driven rule engine (no NL parsing, no AI).

Rules are CODE-DEFINED defaults (customer-agnostic) with per-rule runtime state in
`rule_state` (enabled flag + config overrides + trigger counters). Evaluation is
idempotent: task-producing rules upsert into `agent_tasks` guarded by
UNIQUE(rule_id, entity_id), and open tasks auto-close when their entity stops
matching (e.g. the RFQ was replied via /admin → status_changed event → re-sync).
"""
import json
from datetime import datetime

from app.database import get_connection
from app.services.audit import write_audit_log
from app.services import website_metrics as metrics


# --------------------------------------------------------------------------- #
# Rule definitions. config values are DEFAULTS — rule_state.config_json overrides.
RULES: list[dict] = [
    {
        "rule_id": "rfq_followup",
        "name": {"en": "RFQ follow-up", "zh": "RFQ 跟进"},
        "description": {
            "en": "Every open RFQ (new/reviewing) gets a follow-up task; overdue or priority-market RFQs are high priority.",
            "zh": "每条未处理 RFQ（new/reviewing）生成跟进任务；超时或重点市场的 RFQ 提升为高优先级。",
        },
        "kind": "followup_task",
        "entity": "rfq",
        "task_type": "follow_up_rfq",
        "config": {"threshold_hours": 24},
    },
    {
        "rule_id": "support_review",
        "name": {"en": "Support request review", "zh": "支持请求处理"},
        "description": {
            "en": "Every open support request gets a review task; overdue ones become high priority.",
            "zh": "每条未处理支持请求生成处理任务；超时升级为高优先级。",
        },
        "kind": "followup_task",
        "entity": "support_request",
        "task_type": "review_support_request",
        "config": {"threshold_hours": 24},
    },
    {
        "rule_id": "download_review",
        "name": {"en": "Download request review", "zh": "资料申请审核"},
        "description": {
            "en": "manual_review download requests (and gated ones not yet fulfilled) get a review task.",
            "zh": "manual_review 资料申请（及未交付的 gated 申请）生成审核任务。",
        },
        "kind": "download_task",
        "entity": "download_request",
        "task_type": "review_download_request",
        "config": {"threshold_hours": 0},
    },
    {
        "rule_id": "category_opportunity",
        "name": {"en": "Product opportunity", "zh": "产品机会"},
        "description": {
            "en": "A product category with several RFQs/download requests within the window flags an opportunity review.",
            "zh": "某产品品类在时间窗内出现多次 RFQ/资料申请，生成机会复盘任务。",
        },
        "kind": "opportunity_task",
        "task_type": "product_opportunity_review",
        "config": {"min_count": 3, "window_days": 7},
    },
    {
        "rule_id": "data_hygiene",
        "name": {"en": "Data hygiene", "zh": "数据治理"},
        "description": {
            "en": "Leads/RFQs missing an email or country get a low-priority cleanup task.",
            "zh": "缺少邮箱或国家的询盘/RFQ 生成低优先级数据补全任务。",
        },
        "kind": "hygiene_task",
        "task_type": "data_hygiene",
        "config": {},
    },
    {
        "rule_id": "priority_countries",
        "name": {"en": "Priority countries", "zh": "重点国家"},
        "description": {
            "en": "RFQs from these countries are boosted to high priority.",
            "zh": "来自这些国家的 RFQ 提升为高优先级。",
        },
        "kind": "modifier",
        "config": {"countries": ["Malaysia", "Vietnam", "Singapore", "Thailand", "Indonesia", "Germany"]},
    },
    {
        "rule_id": "priority_categories",
        "name": {"en": "Priority product categories", "zh": "重点产品品类"},
        "description": {
            "en": "RFQs for these categories are boosted to high priority.",
            "zh": "这些品类的 RFQ 提升为高优先级。",
        },
        "kind": "modifier",
        "config": {
            "categories": [
                "area-scan-cameras", "smart-vision-sensors", "code-reading-cameras",
                "barcode-scanners", "android-pda", "proximity-sensors",
                "laser-measurement", "dimensional-gauges",
            ]
        },
    },
    {
        "rule_id": "rfq_surge_daily",
        "name": {"en": "Daily RFQ surge", "zh": "单日 RFQ 爆量"},
        "description": {
            "en": "A day with unusually many RFQs is flagged in the daily report.",
            "zh": "单日 RFQ 数量异常时在日报中预警。",
        },
        "kind": "report_flag",
        "config": {"min_per_day": 3},
    },
    {
        "rule_id": "repeat_inquirer",
        "name": {"en": "Repeat inquirer (high intent)", "zh": "重复询盘（高意向）"},
        "description": {
            "en": "The same email submitting multiple times is flagged as high intent in reports.",
            "zh": "同一邮箱多次提交标记为高意向，进入报告。",
        },
        "kind": "report_flag",
        "config": {"min_count": 2},
    },
    {
        "rule_id": "cart_abandonment",
        "name": {"en": "Cart abandonment lead", "zh": "弃购线索"},
        "description": {
            "en": "cart.added with no quote.requested for the same product within the window → daily-report lead entry.",
            "zh": "加购后时间窗内无询价 → 弃购线索进入日报。",
        },
        "kind": "report_flag",
        "config": {"window_hours": 48},
    },
    {
        "rule_id": "paid_not_fulfilled",
        "name": {"en": "Paid but not fulfilled", "zh": "已付款未发货"},
        "description": {
            "en": "Orders paid for more than N days without fulfilment get a high-priority task.",
            "zh": "订单已付款超过 N 天未发货，生成高优先级任务。",
        },
        "kind": "commerce_task",
        "task_type": "fulfil_order",
        "config": {"threshold_days": 7},
    },
    {
        "rule_id": "high_views_no_inquiry",
        "name": {"en": "High views, no inquiry", "zh": "高浏览零询盘"},
        "description": {
            "en": "Shop products viewed many times with no cart/quote signal get an opportunity task.",
            "zh": "商城产品高浏览但无加购/询价，生成产品机会任务。",
        },
        "kind": "commerce_task",
        "task_type": "product_opportunity_review",
        "config": {"min_views": 5},
    },
    {
        "rule_id": "exclude_internal_tests",
        "name": {"en": "Exclude internal tests", "zh": "排除内部测试"},
        "description": {
            "en": "spam rows and internal-test markers are excluded from all report metrics (raw data is kept).",
            "zh": "spam 与内部测试标记的数据不进入报告指标（原始数据保留，审计链不破坏）。",
        },
        "kind": "exclusion",
        "config": dict(metrics.DEFAULT_EXCLUSIONS),
    },
]

RULE_INDEX = {r["rule_id"]: r for r in RULES}


def ensure_rule_state() -> None:
    """Seed a rule_state row per defined rule (idempotent)."""
    with get_connection() as connection:
        for rule in RULES:
            connection.execute(
                "INSERT OR IGNORE INTO rule_state (rule_id, enabled, config_json) VALUES (?, 1, ?)",
                (rule["rule_id"], json.dumps(rule["config"], ensure_ascii=False)),
            )
        connection.commit()


def rule_runtime(rule_id: str, customer_id: str | None = None) -> tuple[bool, dict]:
    """(enabled, effective_config). Three config layers: code defaults <
    rule_state overrides < per-customer thresholds (customers.config_json)."""
    base = dict(RULE_INDEX[rule_id]["config"])
    with get_connection() as connection:
        row = connection.execute("SELECT enabled, config_json FROM rule_state WHERE rule_id = ?", (rule_id,)).fetchone()
    enabled = True
    if row is not None:
        enabled = bool(row["enabled"])
        try:
            base.update(json.loads(row["config_json"] or "{}"))
        except json.JSONDecodeError:
            pass
    if customer_id:
        from app.services.customers import customer_rule_threshold

        base.update(customer_rule_threshold(customer_id, rule_id))
    return enabled, base


def list_rules_with_state() -> list[dict]:
    ensure_rule_state()
    with get_connection() as connection:
        states = {row["rule_id"]: dict(row) for row in connection.execute("SELECT * FROM rule_state").fetchall()}
    out = []
    for rule in RULES:
        state = states.get(rule["rule_id"], {})
        out.append(
            {
                "rule_id": rule["rule_id"],
                "name": rule["name"],
                "description": rule["description"],
                "kind": rule["kind"],
                "enabled": bool(state.get("enabled", 1)),
                "config": json.loads(state.get("config_json") or "{}") or rule["config"],
                "last_triggered_at": state.get("last_triggered_at"),
                "triggered_count": state.get("triggered_count", 0),
            }
        )
    return out


def set_rule_enabled(rule_id: str, enabled: bool) -> None:
    if rule_id not in RULE_INDEX:
        raise KeyError(f"Unknown rule: {rule_id}")
    ensure_rule_state()
    with get_connection() as connection:
        connection.execute(
            "UPDATE rule_state SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE rule_id = ?",
            (1 if enabled else 0, rule_id),
        )
        connection.commit()
    write_audit_log("rule_toggled", "business_rule", target_id=rule_id, risk_level="medium", output_summary=f"enabled={enabled}")


# ------------------------------ priority boost ------------------------------ #
def _priority_for(item: dict, base: str, overdue: bool) -> str:
    if overdue:
        return "high"
    enabled_c, cfg_c = rule_runtime("priority_countries")
    if enabled_c and (item["data"].get("country") or "") in (cfg_c.get("countries") or []):
        return "high"
    enabled_p, cfg_p = rule_runtime("priority_categories")
    if enabled_p and (item["data"].get("product_category") or "") in (cfg_p.get("categories") or []):
        return "high"
    return base


# ------------------------------- task creation ------------------------------ #
def _create_task(connection, *, rule_id: str, task_type: str, entity_type: str, entity_id: str,
                 title: str, description: str, priority: str, recommendation: str,
                 source: str = "gyutron-website") -> int | None:
    """Idempotent insert (UNIQUE rule_id+entity_id). Returns task id when created."""
    cursor = connection.execute(
        """
        INSERT OR IGNORE INTO agent_tasks
          (title, description, task_type, priority, status, source, entity_type, entity_id, rule_id, recommendation_text)
        VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)
        """,
        (title, description, task_type, priority, source, entity_type, entity_id, rule_id, recommendation),
    )
    if cursor.rowcount == 0:
        return None
    task_id = cursor.lastrowid
    connection.execute(
        "INSERT INTO rule_triggers (rule_id, entity_type, entity_id, output_type, output_id) VALUES (?, ?, ?, 'task', ?)",
        (rule_id, entity_type, entity_id, str(task_id)),
    )
    connection.execute(
        "UPDATE rule_state SET last_triggered_at = CURRENT_TIMESTAMP, triggered_count = triggered_count + 1, updated_at = CURRENT_TIMESTAMP WHERE rule_id = ?",
        (rule_id,),
    )
    return task_id


def _label(item: dict) -> str:
    who = item["data"].get("company") or item["data"].get("email") or "?"
    extra = item["data"].get("product_category") or item["data"].get("product_model") or item["data"].get("issue_type") or ""
    return f"{who}" + (f" · {extra}" if extra else "")


def evaluate_rules(connector_id: int | None = None, customer_id: str | None = None) -> dict:
    """Run all enabled task-producing rules. customer_id scopes the data to that
    customer's sources and applies its threshold overrides. Returns counters."""
    ensure_rule_state()
    sources = None
    if customer_id:
        from app.services.customers import customer_sources

        sources = customer_sources(customer_id)
    records = metrics.load_records(connector_id, sources=sources)
    created = 0
    auto_closed = 0
    # auto-close must NEVER touch tasks outside this evaluation's scope — a
    # connector- or customer-scoped run only sees ITS rows, so an unscoped
    # close would wrongly kill other customers' open tasks.
    close_scope = sources if sources is not None else (sorted({r["source"] for r in records}) if connector_id else None)

    with get_connection() as connection:
        # 1/2. follow-up rules (rfq + support)
        for rule_id in ("rfq_followup", "support_review"):
            enabled, cfg = rule_runtime(rule_id, customer_id)
            if not enabled:
                continue
            rule = RULE_INDEX[rule_id]
            threshold = float(cfg.get("threshold_hours", 24))
            matching_ids = set()
            for item in records:
                if item["type"] != rule["entity"] or item["status"] not in metrics.OPEN_STATUSES:
                    continue
                matching_ids.add(item["id"])
                hours = metrics.waiting_hours(item) or 0
                overdue = hours >= threshold
                priority = _priority_for(item, "medium", overdue)
                wait_note = f"waiting {hours:.0f}h" if hours >= 1 else "new"
                if _create_task(
                    connection,
                    rule_id=rule_id,
                    task_type=rule["task_type"],
                    entity_type=rule["entity"],
                    entity_id=item["id"],
                    title=f"Follow up {item['id']}",
                    description=f"{_label(item)} — status {item['status']}, {wait_note}.",
                    priority=priority,
                    recommendation=f"Reply to {item['data'].get('email') or 'the requester'} and move {item['id']} out of '{item['status']}'.",
                    source=item.get("source") or "gyutron-website",
                ):
                    created += 1
            auto_closed += _auto_close(connection, rule_id, matching_ids)

        # 3. download review
        enabled, cfg = rule_runtime("download_review", customer_id)
        if enabled:
            matching_ids = set()
            for item in records:
                if item["type"] != "download_request":
                    continue
                access = item["data"].get("access_type") or "manual_review"
                pending = (access == "manual_review" and item["status"] in ("new", "approved")) or (
                    access == "gated" and item["status"] in ("new", "approved")
                )
                if not pending:
                    continue
                matching_ids.add(item["id"])
                if _create_task(
                    connection,
                    rule_id="download_review",
                    task_type="review_download_request",
                    entity_type="download_request",
                    entity_id=item["id"],
                    title=f"Review download request {item['id']}",
                    description=f"{_label(item)} — {item['data'].get('requested_file') or '?'} ({access}).",
                    priority=_priority_for(item, "medium", False),
                    recommendation="Verify the requester, then send the document or approve/reject in /admin.",
                    source=item.get("source") or "gyutron-website",
                ):
                    created += 1
            auto_closed += _auto_close(connection, "download_review", matching_ids, close_scope)

        # 4. category opportunity (entity = category slug)
        enabled, cfg = rule_runtime("category_opportunity", customer_id)
        if enabled:
            window_days = int(cfg.get("window_days", 7))
            min_count = int(cfg.get("min_count", 3))
            recent = metrics.load_records(connector_id, time_range="7d" if window_days <= 7 else "30d", sources=sources)
            counter: dict = {}
            for item in recent:
                if item["type"] in ("rfq", "download_request"):
                    cat = item["data"].get("product_category") or ""
                    if cat:
                        counter[cat] = counter.get(cat, 0) + 1
            for cat, n in counter.items():
                if n < min_count:
                    continue
                if _create_task(
                    connection,
                    rule_id="category_opportunity",
                    task_type="product_opportunity_review",
                    entity_type="product_category",
                    entity_id=f"{cat}",
                    title=f"Product opportunity: {cat}",
                    description=f"{n} RFQ/download signals for '{cat}' in the last {window_days} days.",
                    priority="medium",
                    recommendation="Review pricing, stock, and content for this category; consider a targeted follow-up.",
                ):
                    created += 1

        # 5. data hygiene
        enabled, _cfg = rule_runtime("data_hygiene", customer_id)
        if enabled:
            for item in records:
                if item["type"] not in ("lead", "rfq"):
                    continue
                problems = []
                if not item["data"].get("email"):
                    problems.append("missing email")
                if not item["data"].get("country"):
                    problems.append("missing country")
                if not problems:
                    continue
                if _create_task(
                    connection,
                    rule_id="data_hygiene",
                    task_type="data_hygiene",
                    entity_type=item["type"],
                    entity_id=item["id"],
                    title=f"Data hygiene: {item['id']}",
                    description=f"{_label(item)} — {', '.join(problems)}.",
                    priority="low",
                    recommendation="Complete the record from the message text or follow up to ask.",
                    source=item.get("source") or "gyutron-website",
                ):
                    created += 1

        # ---- commerce rules (Phase 4) ----
        from app.services import commerce_metrics

        enabled, cfg = rule_runtime("paid_not_fulfilled", customer_id)
        if enabled:
            stale = commerce_metrics.paid_not_fulfilled(int(cfg.get("threshold_days", 7)), sources=sources)
            matching = {f"{o['source']}:{o['external_id']}" for o in stale}
            for o in stale:
                if _create_task(
                    connection,
                    rule_id="paid_not_fulfilled",
                    task_type="fulfil_order",
                    entity_type="order",
                    entity_id=f"{o['source']}:{o['external_id']}",
                    title=f"Fulfil order {o.get('order_number') or o['external_id']}",
                    description=f"{o['source']} — paid {o.get('amount_base') or o.get('total_amount')} ({o.get('currency')}), created {o.get('created_at_source') or '?'}.",
                    priority="high",
                    recommendation="Ship or update the order status in the source system; the workspace is read-only.",
                ):
                    created += 1
            auto_closed += _auto_close(connection, "paid_not_fulfilled", matching, close_scope)

        enabled, cfg = rule_runtime("high_views_no_inquiry", customer_id)
        if enabled:
            hot = commerce_metrics.high_views_no_inquiry(int(cfg.get("min_views", 5)))
            for handle, views in hot:
                if _create_task(
                    connection,
                    rule_id="high_views_no_inquiry",
                    task_type="product_opportunity_review",
                    entity_type="product_handle",
                    entity_id=handle,
                    title=f"High views, no inquiry: {handle}",
                    description=f"{views} shop views with no cart/quote signal.",
                    priority="medium",
                    recommendation="Check pricing/content for this product; consider a targeted promotion.",
                ):
                    created += 1

        connection.commit()

    if created:
        write_audit_log("rules_evaluated", "business_rule", risk_level="low", output_summary=f"{created} task(s) created, {auto_closed} auto-closed")
    return {"tasks_created": created, "tasks_auto_closed": auto_closed}


def _auto_close(connection, rule_id: str, still_matching: set, scope_sources: list | None = None) -> int:
    """Close open tasks whose entity no longer matches the rule (loop closure).
    scope_sources limits closure to tasks from the sources this run evaluated."""
    query = "SELECT id, entity_id FROM agent_tasks WHERE rule_id = ? AND status = 'open'"
    params: list = [rule_id]
    if scope_sources is not None:
        placeholders = ", ".join("?" for _ in scope_sources) or "''"
        query += f" AND source IN ({placeholders})"
        params.extend(scope_sources)
    rows = connection.execute(query, params).fetchall()
    closed = 0
    for row in rows:
        if row["entity_id"] in still_matching:
            continue
        connection.execute(
            "UPDATE agent_tasks SET status = 'done', updated_at = CURRENT_TIMESTAMP, "
            "recommendation_text = COALESCE(recommendation_text, '') || ' [auto-closed: entity no longer matches the rule]' WHERE id = ?",
            (row["id"],),
        )
        closed += 1
    return closed


# ------------------------------ report flags -------------------------------- #
def report_flags(connector_id: int | None = None) -> dict:
    """Computed flags consumed by the report generators (no persistence)."""
    flags: dict = {"surge_days": [], "repeat_inquirers": []}
    enabled, cfg = rule_runtime("rfq_surge_daily")
    if enabled:
        records = metrics.load_records(connector_id, time_range="7d")
        for day, n in metrics.day_counts(records, types=("rfq",), days=7):
            if n >= int(cfg.get("min_per_day", 3)):
                flags["surge_days"].append({"day": day, "count": n})
    enabled, cfg = rule_runtime("repeat_inquirer")
    if enabled:
        records = metrics.load_records(connector_id, time_range="30d")
        flags["repeat_inquirers"] = [
            {"email": email, "count": n} for email, n in metrics.repeat_emails(records, min_count=int(cfg.get("min_count", 2)))
        ]
    enabled, cfg = rule_runtime("cart_abandonment")
    flags["abandoned_carts"] = []
    if enabled:
        from app.services import commerce_metrics

        flags["abandoned_carts"] = [
            {"product_handle": e.get("product_handle"), "occurred_at": e.get("occurred_at")}
            for e in commerce_metrics.abandoned_carts(int(cfg.get("window_hours", 48)))[:10]
        ]
    return flags
