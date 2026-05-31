import { useEffect, useState } from "react";

import { getSystemHealth } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { SystemHealth as SystemHealthType } from "../types/api";

export function SystemHealth() {
  const [health, setHealth] = useState<SystemHealthType>();

  useEffect(() => {
    getSystemHealth().then(setHealth).catch(() => undefined);
  }, []);

  return (
    <div className="page-stack">
      <PageHeader title="System Health" eyebrow="Local operations" description="Monitor backend, database, scheduler, backup, sync, disk usage, and recent errors." />
      <section className="metric-grid compact">
        <div className="mini-metric"><span>Backend</span><strong>{health?.backend ?? "-"}</strong></div>
        <div className="mini-metric"><span>Database</span><strong>{health?.database ?? "-"}</strong></div>
        <div className="mini-metric"><span>Scheduler</span><strong>{health?.scheduler ?? "-"}</strong></div>
        <div className="mini-metric"><span>Automations</span><strong>{health?.active_automations ?? 0}</strong></div>
        <div className="mini-metric"><span>Disk free</span><strong>{health ? `${Math.round(health.disk_usage.free / 1024 / 1024)} MB` : "-"}</strong></div>
      </section>
      <section className="panel">
        <div className="panel-heading"><h2>Recent errors</h2><StatusBadge label={`${health?.recent_errors.length ?? 0} records`} tone="neutral" /></div>
        <div className="list-stack">
          {health?.recent_errors.map((item) => <article className="list-item" key={item.id}><div><strong>{item.action}</strong><span>{item.output_summary ?? item.input_summary}</span></div></article>)}
        </div>
      </section>
    </div>
  );
}
