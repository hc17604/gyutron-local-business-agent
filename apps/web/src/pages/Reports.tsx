import { FilePlus2 } from "lucide-react";

import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { ReportViewer } from "../components/reports/ReportViewer";
import { reports } from "../data/mockDashboard";

export function Reports() {
  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" type="button">
            <FilePlus2 size={16} />
            Generate Report
          </button>
        }
        description="Manage owner daily reports, weekly reports, monthly reports, and custom analyses."
        eyebrow="Local report history"
        title="Reports"
      />

      <section className="grid two-columns">
        <article className="panel">
          <div className="panel-heading">
            <h2>Report list</h2>
          </div>
          <div className="list-stack">
            {reports.map((report) => (
              <article className="record-card" key={report.title}>
                <div>
                  <strong>{report.title}</strong>
                  <span>
                    {report.type} · {report.sourceFiles} · {report.createdAt}
                  </span>
                </div>
                <StatusBadge label={report.status} tone={report.status === "Ready" ? "success" : "warning"} />
              </article>
            ))}
          </div>
        </article>
        <ReportViewer />
      </section>
    </div>
  );
}
