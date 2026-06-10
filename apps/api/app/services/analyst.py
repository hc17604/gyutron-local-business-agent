"""AI Analyst Layer (Phase 6) — explanations, executive summaries, follow-up drafts.

DETERMINISTIC by design (Phase-3 principle: fully usable with NO model
configured); a configured LLM may optionally REPHRASE these outputs later (hook:
app/llm), but correctness never depends on it. Safety boundary: explains and
drafts ONLY — never sends email/WhatsApp, never writes back to source systems,
never includes data from another customer (inputs are pre-scoped by customer).
"""
import json

from app.database import get_connection
from app.services.customers import customer_sources, get_customer


# rule_id → bilingual explanation templates (what / why / suggested action)
RULE_EXPLAIN = {
    "rfq_followup": {
        "what": {"en": "An RFQ is waiting for a reply", "zh": "一条 RFQ 等待回复"},
        "why": {"en": "RFQs convert best within 24h; waiting longer sharply lowers win rate.",
                "zh": "RFQ 在 24 小时内响应转化率最高，拖得越久赢单率越低。"},
        "action": {"en": "Reply with pricing/availability today and move the status out of 'new'.",
                   "zh": "今天回复价格/交期，并把状态从 new 推进。"},
    },
    "support_review": {
        "what": {"en": "A support request is unanswered", "zh": "一条支持请求未处理"},
        "why": {"en": "Support speed drives reorder behavior and reputation.",
                "zh": "售后响应速度直接影响复购与口碑。"},
        "action": {"en": "Acknowledge the customer and assign an engineer.",
                   "zh": "先回复客户确认收到，并指派工程师。"},
    },
    "download_review": {
        "what": {"en": "A document request awaits review", "zh": "一条资料申请待审核"},
        "why": {"en": "Datasheet requesters are active evaluators — fast delivery keeps you in the shortlist.",
                "zh": "索取资料的客户正处于选型阶段——快速交付才能留在候选名单。"},
        "action": {"en": "Verify the requester and send the document (or approve in /admin).",
                   "zh": "核实申请人后发送资料（或在 /admin 批准）。"},
    },
    "paid_not_fulfilled": {
        "what": {"en": "A paid order has not shipped", "zh": "一笔已付款订单未发货"},
        "why": {"en": "Paid-but-unfulfilled orders are the top driver of disputes and refunds.",
                "zh": "已付款未发货是纠纷与退款的头号来源。"},
        "action": {"en": "Ship it or update the order status in the source system (workspace is read-only).",
                   "zh": "尽快发货，或在源系统更新订单状态（中台只读）。"},
    },
    "high_views_no_inquiry": {
        "what": {"en": "A product gets views but no inquiries", "zh": "一款产品高浏览但零询盘"},
        "why": {"en": "Interest without conversion usually means price/content/CTA friction.",
                "zh": "有兴趣无转化，通常是价格、内容或行动入口的问题。"},
        "action": {"en": "Review the product page price/content; consider a targeted promotion.",
                   "zh": "检查产品页价格与内容，考虑定向推广。"},
    },
    "category_opportunity": {
        "what": {"en": "A category shows repeated demand signals", "zh": "一个品类出现多次需求信号"},
        "why": {"en": "Clustered RFQ/download signals indicate a market window.",
                "zh": "集中出现的询价/资料信号意味着市场窗口。"},
        "action": {"en": "Review stock, pricing and content for the category; brief sales.",
                   "zh": "复盘该品类库存/定价/内容，并向销售同步。"},
    },
    "data_hygiene": {
        "what": {"en": "A lead record is incomplete", "zh": "一条线索记录不完整"},
        "why": {"en": "Missing email/country blocks follow-up and skews reports.",
                "zh": "缺邮箱/国家会卡住跟进并影响报表。"},
        "action": {"en": "Complete the record from the message text or ask the requester.",
                   "zh": "从留言内容补全，或向客户确认。"},
    },
}


def explain_task(task: dict, language: str = "en") -> dict:
    """Deterministic explanation for a rule-generated task (action card core)."""
    zh = (language or "en").lower().startswith("zh")
    lang = "zh" if zh else "en"
    tpl = RULE_EXPLAIN.get(task.get("rule_id") or "", None)
    if tpl is None:
        tpl = {"what": {"en": "A rule produced this task", "zh": "规则生成了该任务"},
               "why": {"en": "See the rule description on the Business Rules page.", "zh": "详见业务规则页中的规则说明。"},
               "action": {"en": task.get("recommendation_text") or "Review the task.", "zh": task.get("recommendation_text") or "请处理该任务。"}}
    return {
        "task_id": task.get("id"),
        "rule_id": task.get("rule_id"),
        "what": tpl["what"][lang],
        "why": tpl["why"][lang],
        "evidence": task.get("description") or "",
        "action": tpl["action"][lang],
        "priority": task.get("priority"),
        "source": task.get("source"),
        "entity_id": task.get("entity_id"),
    }


def followup_drafts(task: dict, customer_id: str | None = None) -> dict:
    """Copy-paste follow-up drafts (en/zh email + WhatsApp). NEVER auto-sent."""
    customer = get_customer(customer_id) if customer_id else None
    brand = (customer or {}).get("brand_name") or "our team"
    entity = task.get("entity_id") or "your request"
    product = ""
    desc = task.get("description") or ""
    if "·" in desc:
        product = desc.split("·", 1)[1].split("—")[0].strip()
    subject_ref = f"{entity}" + (f" ({product})" if product else "")
    return {
        "email_en": (
            f"Subject: Your inquiry {subject_ref}\n\n"
            f"Hello,\n\nThank you for your inquiry. I'm following up on {subject_ref} — "
            f"could you share your target quantity and timeline so we can prepare exact pricing and lead time?\n\n"
            f"Best regards,\n{brand}"
        ),
        "email_zh": (
            f"主题：关于您的询价 {subject_ref}\n\n"
            f"您好！\n\n感谢您的咨询。关于 {subject_ref}，方便告知目标数量与期望交期吗？我们将为您准备准确的报价与货期。\n\n"
            f"祝好，\n{brand}"
        ),
        "whatsapp": f"Hi! Following up on {subject_ref} — happy to send pricing once we know your quantity & timeline. — {brand}",
        "auto_send": False,
    }


def executive_summary(stats: dict, language: str = "en") -> str:
    """Deterministic executive-summary paragraph for the daily report header."""
    zh = (language or "en").lower().startswith("zh")
    y = stats.get("yesterday", {})
    total_y = sum(y.values()) if isinstance(y, dict) else 0
    overdue = stats.get("overdue", 0)
    open_tasks = stats.get("open_tasks", 0)
    flags = stats.get("flags", {}) or {}
    risk_n = len(flags.get("surge_days", [])) + len(flags.get("abandoned_carts", []))
    opp_n = len(flags.get("repeat_inquirers", []))
    if zh:
        parts = [f"昨日新增 {total_y} 条线索。"]
        parts.append(f"当前 {overdue} 条超时未跟进、{open_tasks} 个待办任务。" if (overdue or open_tasks) else "暂无超时项与积压任务。")
        if risk_n:
            parts.append(f"{risk_n} 个风险信号需要注意。")
        if opp_n:
            parts.append(f"{opp_n} 个高意向机会值得优先跟进。")
        parts.append("优先级：先清超时项，再跟进高意向客户。" if (overdue or opp_n) else "保持当前节奏即可。")
        return "".join(parts)
    parts = [f"{total_y} new lead(s) yesterday. "]
    parts.append(f"{overdue} overdue follow-up(s) and {open_tasks} open task(s) need attention. " if (overdue or open_tasks) else "No overdue items or backlog. ")
    if risk_n:
        parts.append(f"{risk_n} risk signal(s) flagged. ")
    if opp_n:
        parts.append(f"{opp_n} high-intent opportunity(ies) worth prioritising. ")
    parts.append("Priority: clear overdue items first, then chase high-intent leads." if (overdue or opp_n) else "Stay the course.")
    return "".join(parts)


def action_cards(customer_id: str, language: str | None = None, limit: int = 8) -> list[dict]:
    """Top open tasks → explained, prioritised action cards with drafts."""
    customer = get_customer(customer_id) or {}
    language = language or customer.get("report_language") or "en"
    sources = customer_sources(customer_id) or []
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM agent_tasks WHERE status='open' AND source IN (%s) "
            "ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, id DESC LIMIT ?"
            % (", ".join("?" for _ in sources) or "''"),
            [*sources, limit],
        ).fetchall()
    cards = []
    for row in rows:
        task = dict(row)
        card = explain_task(task, language)
        card["customer_id"] = customer_id
        if task.get("rule_id") in ("rfq_followup", "support_review", "download_review"):
            card["drafts"] = followup_drafts(task, customer_id)
        cards.append(card)
    return cards
