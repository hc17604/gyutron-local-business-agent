import { CalendarDays, ClipboardCopy, FileBarChart, FilePlus2, TrendingUp } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { generateNamedReport, generateWebsiteLeadsSummary, getReports } from "../api/client";
import { getCurrentLanguage } from "../i18n";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState } from "../components/common/EmptyState";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { formatStatus } from "../i18n/formatters";
import type { LocalReport } from "../types/api";

export function Reports() {
  const { t } = useTranslation();
  const [reports, setReports] = useState<LocalReport[]>([]);
  const [selected, setSelected] = useState<LocalReport>();
  const [message, setMessage] = useState<string>();

  async function refresh() {
    const response = await getReports();
    setReports(response.reports);
    if (response.reports.length) setSelected((current) => current ?? response.reports[0]);
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function generate(kind: "daily-owner" | "weekly-pipeline" | "opportunities" | "leads-summary") {
    const language = getCurrentLanguage();
    const result =
      kind === "leads-summary"
        ? await generateWebsiteLeadsSummary({ language, time_range: "30d" })
        : await generateNamedReport(kind, { language });
    setMessage(result.summary);
    setSelected(undefined);
    await refresh();
  }

  async function copyMarkdown() {
    if (!selected?.content_markdown) return;
    await navigator.clipboard.writeText(selected.content_markdown);
    setMessage(t("reports.copied"));
  }

  const buttons: Array<{ kind: "daily-owner" | "weekly-pipeline" | "opportunities" | "leads-summary"; label: string; icon: ReactNode }> = [
    { kind: "daily-owner", label: t("reports.dailyOwner"), icon: <FilePlus2 size={16} /> },
    { kind: "weekly-pipeline", label: t("reports.weeklyPipeline"), icon: <CalendarDays size={16} /> },
    { kind: "leads-summary", label: t("reports.leadsSummary"), icon: <FileBarChart size={16} /> },
    { kind: "opportunities", label: t("reports.opportunities"), icon: <TrendingUp size={16} /> },
  ];

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <>
            {buttons.map((b) => (
              <button className="button primary" key={b.kind} onClick={() => void generate(b.kind).catch((error: Error) => setMessage(error.message))} type="button">
                {b.icon}
                {b.label}
              </button>
            ))}
          </>
        }
        description={t("reports.description")}
        eyebrow={t("reports.eyebrow")}
        title={t("reports.title")}
      />
      {message ? <div className="inline-info">{message}</div> : null}

      <section className="grid two-columns">
        <article className="panel">
          <SectionHeader title={t("reports.reportList")} meta={t("reports.localDatabase")} />
          <div className="list-stack">
            {reports.length ? (
              reports.map((report) => (
                <article
                  className="record-card"
                  key={report.id}
                  onClick={() => setSelected(report)}
                  style={{ cursor: "pointer", outline: selected?.id === report.id ? "2px solid var(--accent, #7c5cd6)" : undefined }}
                >
                  <div>
                    <strong>{report.title}</strong>
                    <span>{report.created_at}</span>
                  </div>
                  <StatusBadge label={formatStatus(report.status, t)} tone={report.status === "ready" ? "success" : "warning"} />
                </article>
              ))
            ) : (
              <EmptyState title={t("reports.noReports")} description={t("reports.noReportsDescription")} />
            )}
          </div>
        </article>

        {selected?.content_markdown ? (
          <article className="report-viewer">
            <div className="report-header-block">
              <p className="eyebrow">{t("reports.generatedLocally")}</p>
              <h2>{selected.title}</h2>
              <span>{selected.created_at}</span>
              <div style={{ marginTop: 8 }}>
                <button className="table-action" onClick={() => void copyMarkdown().catch((error: Error) => setMessage(error.message))} type="button">
                  <ClipboardCopy size={14} />
                  {t("reports.copyMarkdown")}
                </button>
              </div>
            </div>
            <div className="report-section-card">
              <pre className="report-markdown" style={{ whiteSpace: "pre-wrap" }}>{selected.content_markdown}</pre>
            </div>
          </article>
        ) : (
          <EmptyState title={t("reports.noReports")} description={t("reports.noReportsDescription")} />
        )}
      </section>
    </div>
  );
}
