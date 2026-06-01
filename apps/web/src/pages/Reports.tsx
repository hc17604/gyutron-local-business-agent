import { FilePlus2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { generateOwnerReport, getReports } from "../api/client";
import { getCurrentLanguage } from "../i18n";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState } from "../components/common/EmptyState";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { ReportViewer } from "../components/reports/ReportViewer";
import { reports as mockReports } from "../data/mockDashboard";
import { formatReportType, formatStatus } from "../i18n/formatters";
import type { LocalReport } from "../types/api";

export function Reports() {
  const { t } = useTranslation();
  const [reports, setReports] = useState<LocalReport[]>([]);
  const [message, setMessage] = useState<string>();

  async function refresh() {
    const response = await getReports();
    setReports(response.reports);
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function handleGenerate() {
    const result = await generateOwnerReport(getCurrentLanguage());
    setMessage(result.summary);
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" onClick={handleGenerate} type="button">
            <FilePlus2 size={16} />
            {t("reports.generateReport")}
          </button>
        }
        description={t("reports.description")}
        eyebrow={t("reports.eyebrow")}
        title={t("reports.title")}
      />
      {message ? <div className="inline-info">{message}</div> : null}

      <section className="grid two-columns">
        <article className="panel">
          <SectionHeader title={t("reports.reportList")} meta={reports.length ? t("reports.localDatabase") : t("reports.demoWorkspace")} />
          <div className="list-stack">
            {reports.length
              ? reports.map((report) => (
                  <article className="record-card" key={report.id}>
                    <div>
                      <strong>{report.title === "Owner Daily Report" ? t("reports.ownerDailyReport") : report.title}</strong>
                      <span>{t("reports.scheduledAutomation")} / {report.created_at}</span>
                    </div>
                    <StatusBadge label={formatStatus(report.status, t)} tone={report.status === "ready" ? "success" : "warning"} />
                  </article>
                ))
              : mockReports.map((report) => (
                  <article className="record-card" key={report.titleKey}>
                    <div>
                      <strong>{t(report.titleKey)}</strong>
                      <span>
                        {formatReportType(report.type, t)} / {report.sourceFiles} / {report.createdAt}
                      </span>
                    </div>
                    <StatusBadge label={formatStatus(report.status, t)} tone={report.status === "ready" ? "success" : "warning"} />
                  </article>
                ))}
          </div>
        </article>
        {reports[0]?.content_markdown ? (
          <article className="report-viewer">
            <div className="report-header-block">
              <p className="eyebrow">{t("reports.ownerReport")}</p>
              <h2>{reports[0].title === "Owner Daily Report" ? t("reports.ownerDailyReport") : reports[0].title}</h2>
              <span>{t("reports.generatedLocally")} / {reports[0].created_at} / {t("reports.language")}: {getCurrentLanguage()}</span>
            </div>
            <div className="report-section-card">
              <h3>{t("reports.executiveSummary")}</h3>
              <p>{reports[0].content_markdown.split("## Owner Summary")[1]?.split("##")[0]?.trim() || reports[0].content_markdown.split("## 老板摘要")[1]?.split("##")[0]?.trim() || t("reports.noSummary")}</p>
            </div>
            <div className="report-section-card warning-callout">
              <h3>{t("reports.risks")}</h3>
              <p>{reports[0].content_markdown.split("## Anomaly Alerts")[1]?.split("##")[0]?.trim() || reports[0].content_markdown.split("## 异常提醒")[1]?.split("##")[0]?.trim() || t("reports.noRisks")}</p>
            </div>
            <div className="report-section-card">
              <h3>{t("reports.actionItems")}</h3>
              <pre className="report-markdown">{reports[0].content_markdown.split("## Sales Follow-up Tasks")[1]?.trim() || reports[0].content_markdown.split("## 销售跟进任务")[1]?.trim() || reports[0].content_markdown}</pre>
            </div>
          </article>
        ) : reports.length || mockReports.length ? (
          <ReportViewer />
        ) : (
          <EmptyState title={t("reports.noReports")} description={t("reports.noReportsDescription")} />
        )}
      </section>
    </div>
  );
}
