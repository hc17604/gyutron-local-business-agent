import { useEffect, useState } from "react";

import { getOverview } from "../api/client";
import { ActionList } from "../components/dashboard/ActionList";
import { AlertList } from "../components/dashboard/AlertList";
import { MetricCard } from "../components/dashboard/MetricCard";
import { PlatformCard } from "../components/dashboard/PlatformCard";
import { alerts, metrics, nextActions, platformPerformance } from "../data/mockDashboard";
import type { OverviewResponse } from "../types/api";

export function Overview() {
  const [overview, setOverview] = useState<OverviewResponse>();

  useEffect(() => {
    getOverview().then(setOverview).catch(() => undefined);
  }, []);

  return (
    <div className="page-stack">
      <section className="metric-grid">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid two-columns">
        <article className="panel agent-summary">
          <div className="panel-heading">
            <h2>Latest Owner Report</h2>
            <span>{overview?.latest_report?.created_at ?? "Generated from local files"}</span>
          </div>
          <p>
            {overview?.latest_report
              ? `Latest report "${overview.latest_report.title}" is ready. ${String(overview.latest_report.summary?.files ?? 0)} local data file(s) were included.`
              : "No scheduled report has been generated yet. Create a Daily Owner Report automation and run it once to populate this summary."}
          </p>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>Automation Status</h2>
            <span>{overview?.active_automations.length ?? 0} rules</span>
          </div>
          <div className="list-stack">
            {(overview?.active_automations ?? []).slice(0, 4).map((rule) => (
              <article className="list-item" key={rule.id}>
                <div>
                  <strong>{rule.name}</strong>
                  <span>{rule.next_run_at ? `Next: ${rule.next_run_at}` : rule.status}</span>
                </div>
              </article>
            ))}
            {!overview?.active_automations.length ? <ActionList actions={nextActions.slice(0, 2)} /> : null}
          </div>
        </article>
      </section>

      <section className="grid two-columns">
        <article className="panel">
          <div className="panel-heading">
            <h2>Recent Sync Status</h2>
            <span>Local connector jobs</span>
          </div>
          <div className="list-stack">
            {(overview?.recent_sync_jobs ?? []).map((job) => (
              <article className="list-item" key={job.id}>
                <div>
                  <strong>{job.status}</strong>
                  <span>
                    {job.records_found} found / {job.records_imported} imported
                  </span>
                </div>
              </article>
            ))}
            {!overview?.recent_sync_jobs.length ? <p className="muted">No connector sync jobs yet.</p> : null}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>Open Alerts</h2>
            <span>{overview?.open_alerts.length ?? alerts.length} active</span>
          </div>
          {overview?.open_alerts.length ? (
            <div className="list-stack">
              {overview.open_alerts.map((alert) => (
                <article className="list-item" key={alert.id}>
                  <div>
                    <strong>{alert.title}</strong>
                    <span>{alert.description}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <AlertList alerts={alerts.slice(0, 2)} />
          )}
        </article>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <h2>Platform Performance</h2>
          <span>Mocked until platform APIs are connected</span>
        </div>
        <div className="platform-strip">
          {platformPerformance.map((platform) => (
            <PlatformCard key={platform.platform} platform={platform} />
          ))}
        </div>
      </section>
    </div>
  );
}
