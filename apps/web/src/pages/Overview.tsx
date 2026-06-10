import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { getCustomers, getDecisionCenter } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { getCurrentLanguage } from "../i18n";
import type { CustomerInfo } from "../types/api";

interface ActionCard {
  task_id?: number;
  rule_id?: string;
  what: string;
  why: string;
  evidence: string;
  action: string;
  priority: string;
  source?: string;
  entity_id?: string;
  drafts?: { email_en: string; email_zh: string; whatsapp: string };
}

interface DecisionData {
  health_status: string;
  today_brief: { new_leads: Record<string, number>; new_orders: number; revenue_today: number; high_priority_actions: number; anomalies: number; suggested: string[] };
  priority_queue: ActionCard[];
  opportunity_radar: Record<string, Record<string, number> | Array<Record<string, unknown>>>;
  risk_watch: Array<{ kind: string; severity: string; detail: string; count: number }>;
  action_cards: ActionCard[];
}

/** Boss Decision Center (Phase 6) — "what do I handle today", not just metrics. */
export function Overview() {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState<CustomerInfo[]>([]);
  const [customerId, setCustomerId] = useState<string>(() => window.localStorage.getItem("gy_dashboard_customer") || "gyutron");
  const [data, setData] = useState<DecisionData>();
  const [message, setMessage] = useState<string>();

  const customer = useMemo(() => customers.find((c) => c.customer_id === customerId), [customers, customerId]);

  useEffect(() => {
    getCustomers().then((r) => setCustomers(r.customers)).catch((e: Error) => setMessage(e.message));
  }, []);

  useEffect(() => {
    window.localStorage.setItem("gy_dashboard_customer", customerId);
    getDecisionCenter(customerId, getCurrentLanguage())
      .then((r) => setData(r as unknown as DecisionData))
      .catch((e: Error) => setMessage(e.message));
  }, [customerId]);

  const tone = (s: string) => (s === "critical" || s === "high" ? "warning" : s === "healthy" ? "success" : "neutral");
  const brief = data?.today_brief;
  const leadsTotal = brief ? Object.values(brief.new_leads).reduce((a, b) => a + b, 0) : 0;

  async function copyDraft(text: string) {
    await navigator.clipboard.writeText(text);
    setMessage(t("decision.draftCopied"));
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <select onChange={(e) => setCustomerId(e.target.value)} value={customerId}>
            {customers.map((c) => (
              <option key={c.customer_id} value={c.customer_id}>{c.display_name}</option>
            ))}
          </select>
        }
        description={t("decision.description")}
        eyebrow={customer?.brand_name || ""}
        title={t("decision.title")}
      />
      {customer?.is_demo ? (
        <div className="inline-info" style={{ borderColor: "#b3261e", color: "#b3261e", fontWeight: 700 }}>{t("dashboard2.demoBanner")}</div>
      ) : null}
      {message ? <div className="inline-info">{message}</div> : null}

      <section className="source-grid">
        <article className="panel"><span className="muted">{t("decision.health")}</span>
          <div><StatusBadge label={data?.health_status ?? "-"} tone={tone(data?.health_status ?? "")} /></div></article>
        <article className="panel"><span className="muted">{t("decision.newLeadsToday")}</span><div style={{ fontSize: 28, fontWeight: 700 }}>{leadsTotal}</div></article>
        <article className="panel"><span className="muted">{t("decision.ordersToday")}</span><div style={{ fontSize: 28, fontWeight: 700 }}>{brief?.new_orders ?? 0}</div>
          <span className="muted">{t("dashboard2.revenue")}: {brief?.revenue_today ?? 0}</span></article>
        <article className="panel"><span className="muted">{t("decision.highPriority")}</span><div style={{ fontSize: 28, fontWeight: 700 }}>{brief?.high_priority_actions ?? 0}</div></article>
        <article className="panel"><span className="muted">{t("decision.anomalies")}</span><div style={{ fontSize: 28, fontWeight: 700 }}>{brief?.anomalies ?? 0}</div></article>
      </section>

      <section className="panel">
        <SectionHeader title={t("decision.actionCards")} description={t("decision.actionCardsDescription")} />
        {data?.action_cards.length ? (
          <div className="list-stack">
            {data.action_cards.map((card) => (
              <article className="record-card" key={`${card.rule_id}-${card.entity_id}`} style={{ alignItems: "flex-start", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <StatusBadge label={card.priority} tone={tone(card.priority)} />
                  <strong>{card.what}</strong>
                  <span className="muted">{card.entity_id} · {card.source}</span>
                </div>
                <div className="muted">{t("decision.why")}: {card.why}</div>
                <div className="muted">{t("decision.evidence")}: {card.evidence}</div>
                <div><strong>{t("decision.action")}:</strong> {card.action}</div>
                {card.drafts ? (
                  <div className="table-actions">
                    <button className="table-action" onClick={() => void copyDraft(card.drafts!.email_en)} type="button">{t("decision.copyEmailEn")}</button>
                    <button className="table-action" onClick={() => void copyDraft(card.drafts!.email_zh)} type="button">{t("decision.copyEmailZh")}</button>
                    <button className="table-action" onClick={() => void copyDraft(card.drafts!.whatsapp)} type="button">{t("decision.whatsapp")}</button>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">{t("decision.noActions")}</p>
        )}
      </section>

      <section className="grid two-columns">
        <article className="panel">
          <SectionHeader title={t("decision.opportunityRadar")} />
          {data ? (
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {Object.entries(data.opportunity_radar).map(([k, v]) => (
                <li key={k}>
                  <strong>{k}</strong>: {Array.isArray(v) ? `${v.length}` : Object.entries(v).map(([a, b]) => `${a}×${b}`).join(", ") || "-"}
                </li>
              ))}
            </ul>
          ) : null}
        </article>
        <article className="panel">
          <SectionHeader title={t("decision.riskWatch")} />
          {data?.risk_watch.length ? (
            <div className="list-stack">
              {data.risk_watch.map((r, i) => (
                <div key={i} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <StatusBadge label={r.severity} tone={tone(r.severity)} />
                  <span>{r.detail}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">{t("decision.noRisks")}</p>
          )}
        </article>
      </section>
    </div>
  );
}
