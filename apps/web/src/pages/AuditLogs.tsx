import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { auditLogs } from "../data/mockDashboard";

export function AuditLogs() {
  return (
    <div className="page-stack">
      <PageHeader
        description="Show local audit records for agent actions, tool calls, report generation, and rule changes."
        eyebrow="Enterprise traceability"
        title="Audit Logs"
      />
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target</th>
                <th>Risk</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={`${log.time}-${log.action}`}>
                  <td>{log.time}</td>
                  <td>{log.actor}</td>
                  <td>{log.action}</td>
                  <td>{log.target}</td>
                  <td>
                    <StatusBadge label={log.risk} tone={log.risk === "High" ? "risk" : log.risk === "Medium" ? "warning" : "success"} />
                  </td>
                  <td>{log.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
