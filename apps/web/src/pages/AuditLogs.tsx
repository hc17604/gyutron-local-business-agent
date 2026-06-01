import { useEffect, useState } from "react";

import { getAuditLogs } from "../api/client";
import { EmptyState } from "../components/common/EmptyState";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { AuditLog } from "../types/api";

export function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    getAuditLogs().then((response) => setLogs(response.audit_logs)).catch(() => undefined);
  }, []);

  return (
    <div className="page-stack">
      <PageHeader description="Show local audit records for logins, model settings, connector syncs, automations, backups, demo data, patch apply, and rollback." eyebrow="Enterprise traceability" title="Audit Logs" />
      <section className="panel">
        <SectionHeader title="Audit trail" description="Every medium or high-risk local action is written here for review." meta={`${logs.length} records`} />
        {logs.length ? <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Time</th><th>Actor</th><th>Action</th><th>Target</th><th>Risk</th><th>Summary</th></tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.created_at}</td>
                  <td>{log.actor}</td>
                  <td>{log.action}</td>
                  <td>{log.target_type}</td>
                  <td><StatusBadge label={log.risk_level} tone={log.risk_level === "high" ? "risk" : log.risk_level === "medium" ? "warning" : "success"} /></td>
                  <td>{log.output_summary ?? log.input_summary ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div> : <EmptyState title="No audit logs yet" description="Logins, connector syncs, reports, backups, and policy changes will appear here automatically." />}
      </section>
    </div>
  );
}
