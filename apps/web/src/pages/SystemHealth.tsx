import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getSystemHealth } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { SystemHealth as SystemHealthType } from "../types/api";

export function SystemHealth() {
  const { t } = useTranslation();
  const [health, setHealth] = useState<SystemHealthType>();

  useEffect(() => {
    getSystemHealth().then(setHealth).catch(() => undefined);
  }, []);

  return (
    <div className="page-stack">
      <PageHeader title={t("systemHealth.title")} eyebrow={t("systemHealth.eyebrow")} description={t("systemHealth.description")} />
      <section className="metric-grid compact">
        <div className="mini-metric"><span>{t("systemHealth.backend")}</span><strong>{health?.backend ?? "-"}</strong></div>
        <div className="mini-metric"><span>{t("systemHealth.database")}</span><strong>{health?.database ?? "-"}</strong></div>
        <div className="mini-metric"><span>{t("systemHealth.scheduler")}</span><strong>{health?.scheduler ?? "-"}</strong></div>
        <div className="mini-metric"><span>{t("systemHealth.automations")}</span><strong>{health?.active_automations ?? 0}</strong></div>
        <div className="mini-metric"><span>{t("systemHealth.diskFree")}</span><strong>{health ? `${Math.round(health.disk_usage.free / 1024 / 1024)} MB` : "-"}</strong></div>
      </section>
      <section className="panel">
        <div className="panel-heading"><h2>{t("systemHealth.recentErrors")}</h2><StatusBadge label={t("auditLogs.records", { count: health?.recent_errors.length ?? 0 })} tone="neutral" /></div>
        <div className="list-stack">
          {health?.recent_errors.map((item) => <article className="list-item" key={item.id}><div><strong>{item.action}</strong><span>{item.output_summary ?? item.input_summary}</span></div></article>)}
        </div>
      </section>
    </div>
  );
}
