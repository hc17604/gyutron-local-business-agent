import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { getCommerceOverview, getCustomers, getReports } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { CustomerInfo, LocalReport } from "../types/api";

interface OverviewData {
  sources: Array<{ source_key: string; display_name: string; is_mock?: number }>;
  leads: Record<string, number>;
  commerce: {
    orders: number;
    revenue_base: number;
    aov_base: number;
    by_country: Record<string, number>;
    top_products: Record<string, number>;
    cart_events: Record<string, number>;
  };
  reconciliation: { paid_payments: number; matched_to_orders: number; unmatched: number };
  open_tasks: number;
}

/** White-label cross-source owner dashboard (Phase 5). Brand name / logo text /
 *  accent color / footer come from the customer config — zero hardcoded brand. */
export function EcommerceDashboard() {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState<CustomerInfo[]>([]);
  const [customerId, setCustomerId] = useState<string>(() => window.localStorage.getItem("gy_dashboard_customer") || "gyutron");
  const [source, setSource] = useState<string>("");
  const [timeRange, setTimeRange] = useState<string>("30d");
  const [data, setData] = useState<OverviewData>();
  const [latestReport, setLatestReport] = useState<LocalReport>();
  const [message, setMessage] = useState<string>();

  const customer = useMemo(() => customers.find((c) => c.customer_id === customerId), [customers, customerId]);

  useEffect(() => {
    getCustomers().then((r) => setCustomers(r.customers)).catch((e: Error) => setMessage(e.message));
  }, []);

  useEffect(() => {
    window.localStorage.setItem("gy_dashboard_customer", customerId);
    getCommerceOverview({ customer_id: customerId, source: source || undefined, time_range: timeRange })
      .then((r) => setData(r as unknown as OverviewData))
      .catch((e: Error) => setMessage(e.message));
    getReports(customerId)
      .then((r) => setLatestReport(r.reports[0]))
      .catch(() => setLatestReport(undefined));
  }, [customerId, source, timeRange]);

  const accent = customer?.accent_color || "#4b2e83";
  const leads = data?.leads ?? {};
  const com = data?.commerce;

  const card = (label: string, value: string | number, sub?: string) => (
    <article className="panel" key={label} style={{ borderTop: `3px solid ${accent}` }}>
      <span className="muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: ".04em" }}>{label}</span>
      <div style={{ fontSize: 30, fontWeight: 700 }}>{value}</div>
      {sub ? <span className="muted" style={{ fontSize: 12 }}>{sub}</span> : null}
    </article>
  );

  const topList = (title: string, entries: Record<string, number> | undefined, empty: string) => (
    <article className="panel">
      <SectionHeader title={title} />
      {entries && Object.keys(entries).length ? (
        <ul className="list-stack" style={{ margin: 0, paddingLeft: 18 }}>
          {Object.entries(entries).slice(0, 6).map(([k, v]) => (
            <li key={k}>{k}: <strong>{v}</strong></li>
          ))}
        </ul>
      ) : (
        <p className="muted">{empty}</p>
      )}
    </article>
  );

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <>
            <select onChange={(e) => { setCustomerId(e.target.value); setSource(""); }} value={customerId}>
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>{c.display_name}</option>
              ))}
            </select>
            <select onChange={(e) => setSource(e.target.value)} value={source}>
              <option value="">{t("dashboard2.allSources")}</option>
              {(data?.sources ?? []).map((s) => (
                <option key={s.source_key} value={s.source_key}>{s.display_name}</option>
              ))}
            </select>
            <select onChange={(e) => setTimeRange(e.target.value)} value={timeRange}>
              <option value="today">{t("dashboard.today")}</option>
              <option value="7d">{t("dashboard.sevenDays")}</option>
              <option value="30d">{t("dashboard.thirtyDays")}</option>
              <option value="all">{t("dashboard2.allTime")}</option>
            </select>
          </>
        }
        description={t("dashboard2.description")}
        eyebrow={customer?.brand_name || ""}
        title={`${customer?.logo_text || customer?.display_name || ""} · ${t("dashboard2.title")}`}
      />
      {customer?.is_demo ? (
        <div className="inline-info" style={{ borderColor: "#b3261e", color: "#b3261e", fontWeight: 700 }}>
          {t("dashboard2.demoBanner")}
        </div>
      ) : null}
      {message ? <div className="inline-info">{message}</div> : null}

      <section className="source-grid">
        {card(t("dashboard2.inquiries"), (leads.lead ?? 0) + (leads.rfq ?? 0), `RFQ ${leads.rfq ?? 0} · ${t("dashboard2.support")} ${leads.support_request ?? 0}`)}
        {card(t("dashboard2.orders"), com?.orders ?? 0)}
        {card(t("dashboard2.revenue"), com?.revenue_base ?? 0, `${t("dashboard2.aov")} ${com?.aov_base ?? 0}`)}
        {card(t("dashboard2.openTasks"), data?.open_tasks ?? 0)}
        {card(
          t("dashboard2.reconciliation"),
          data ? `${data.reconciliation.matched_to_orders}/${data.reconciliation.paid_payments}` : "-",
          data?.reconciliation.unmatched ? `${data.reconciliation.unmatched} ${t("dashboard2.unmatched")}` : "OK",
        )}
      </section>

      <section className="grid two-columns">
        {topList(t("dashboard2.topProducts"), com?.top_products, t("dashboard2.noData"))}
        {topList(t("dashboard2.byCountry"), com?.by_country, t("dashboard2.noData"))}
      </section>

      <section className="grid two-columns">
        {topList(t("dashboard2.cartEvents"), com?.cart_events, t("dashboard2.noData"))}
        <article className="panel">
          <SectionHeader title={t("dashboard2.latestReport")} meta={latestReport?.created_at} />
          {latestReport ? (
            <>
              <strong>{latestReport.title}</strong>
              <StatusBadge label={latestReport.status} tone={latestReport.status === "ready" ? "success" : "warning"} />
              <pre className="report-markdown" style={{ whiteSpace: "pre-wrap", maxHeight: 240, overflow: "auto" }}>
                {latestReport.content_markdown?.slice(0, 900)}
              </pre>
            </>
          ) : (
            <p className="muted">{t("dashboard2.noReport")}</p>
          )}
        </article>
      </section>

      <footer className="muted" style={{ fontSize: 12, padding: "8px 2px" }}>{customer?.footer_legal || ""}</footer>
    </div>
  );
}
