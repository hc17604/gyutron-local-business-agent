import { FilePlus2 } from "lucide-react";
import { useEffect, useState } from "react";

import { generateOwnerReport, getReports } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
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
          <div className="panel-heading">
            <h2>Report list</h2>
            <span>{reports.length ? "Local database" : "Mock samples"}</span>
          </div>
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
            <h2>{reports[0].title}</h2>
            <pre className="report-markdown">{reports[0].content_markdown}</pre>
          </article>
        ) : (
          <ReportViewer />
        )}
      </section>
    </div>
  );
}
