import { FilePlus2 } from "lucide-react";
import { useEffect, useState } from "react";

import { generateOwnerReport, getReports } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState } from "../components/common/EmptyState";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { ReportViewer } from "../components/reports/ReportViewer";
import { reports as mockReports } from "../data/mockDashboard";
import type { LocalReport } from "../types/api";

export function Reports() {
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
    const result = await generateOwnerReport();
    setMessage(result.summary);
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" onClick={handleGenerate} type="button">
            <FilePlus2 size={16} />
            Generate Report
          </button>
        }
        description="Manage owner daily reports, scheduled reports, and Agent-generated analyses."
        eyebrow="Local report history"
        title="Reports"
      />
      {message ? <div className="inline-info">{message}</div> : null}

      <section className="grid two-columns">
        <article className="panel">
          <SectionHeader title="Report list" meta={reports.length ? "Local database" : "Demo workspace"} />
          <div className="list-stack">
            {reports.length
              ? reports.map((report) => (
                  <article className="record-card" key={report.id}>
                    <div>
                      <strong>{report.title}</strong>
                      <span>Scheduled / Automation / {report.created_at}</span>
                    </div>
                    <StatusBadge label={report.status} tone={report.status === "ready" ? "success" : "warning"} />
                  </article>
                ))
              : mockReports.map((report) => (
                  <article className="record-card" key={report.title}>
                    <div>
                      <strong>{report.title}</strong>
                      <span>
                        {report.type} / {report.sourceFiles} / {report.createdAt}
                      </span>
                    </div>
                    <StatusBadge label={report.status} tone={report.status === "Ready" ? "success" : "warning"} />
                  </article>
                ))}
          </div>
        </article>
        {reports[0]?.content_markdown ? (
          <article className="report-viewer">
            <div className="report-header-block">
              <p className="eyebrow">Owner report</p>
              <h2>{reports[0].title}</h2>
              <span>Generated locally / {reports[0].created_at}</span>
            </div>
            <div className="report-section-card">
              <h3>Executive Summary</h3>
              <p>{reports[0].content_markdown.split("## Owner Summary")[1]?.split("##")[0]?.trim() || "No summary available yet."}</p>
            </div>
            <div className="report-section-card warning-callout">
              <h3>Risks</h3>
              <p>{reports[0].content_markdown.split("## Anomaly Alerts")[1]?.split("##")[0]?.trim() || "No risks found."}</p>
            </div>
            <div className="report-section-card">
              <h3>Action Items</h3>
              <pre className="report-markdown">{reports[0].content_markdown.split("## Sales Follow-up Tasks")[1]?.trim() || reports[0].content_markdown}</pre>
            </div>
          </article>
        ) : reports.length || mockReports.length ? (
          <ReportViewer />
        ) : (
          <EmptyState title="No reports yet" description="Generate the first owner daily report from local connector data." />
        )}
      </section>
    </div>
  );
}
