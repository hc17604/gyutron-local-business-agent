import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getAuditLogs } from "../api/client";
import { EmptyState } from "../components/common/EmptyState";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { AuditLog } from "../types/api";

export function AuditLogs() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    getAuditLogs().then((response) => setLogs(response.audit_logs)).catch(() => undefined);
  }, []);

  return (
    <div className="page-stack">
      <PageHeader description={t("auditLogs.description")} eyebrow={t("auditLogs.eyebrow")} title={t("auditLogs.title")} />
      <section className="panel">
        <SectionHeader title={t("auditLogs.auditTrail")} description={t("auditLogs.auditTrailDescription")} meta={t("auditLogs.records", { count: logs.length })} />
        {logs.length ? <div className="table-wrap">
          <table>
            <thead>
              <tr><th>{t("auditLogs.time")}</th><th>{t("auditLogs.actor")}</th><th>{t("auditLogs.action")}</th><th>{t("auditLogs.target")}</th><th>{t("auditLogs.risk")}</th><th>{t("auditLogs.summary")}</th></tr>
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
        </div> : <EmptyState title={t("auditLogs.noLogs")} description={t("auditLogs.noLogsDescription")} />}
      </section>
    </div>
  );
}
