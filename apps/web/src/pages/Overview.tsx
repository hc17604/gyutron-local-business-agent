import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getOverview } from "../api/client";
import { ActionList } from "../components/dashboard/ActionList";
import { AlertList } from "../components/dashboard/AlertList";
import { MetricCard } from "../components/dashboard/MetricCard";
import { PlatformCard } from "../components/dashboard/PlatformCard";
import { StatusBadge } from "../components/common/StatusBadge";
import { alerts, metrics, nextActions, platformPerformance } from "../data/mockDashboard";
import { formatCountry, formatSeverity, formatStatus } from "../i18n/formatters";
import type { OverviewResponse } from "../types/api";

export function Overview() {
  const { i18n, t } = useTranslation();
  const [overview, setOverview] = useState<OverviewResponse>();

  useEffect(() => {
    getOverview().then(setOverview).catch(() => undefined);
  }, []);

  function formatAlertTitle(title: string) {
    if (title === "24h no follow-up") {
      return t("alerts.noFollowup24h");
    }
    if (title === "Inventory low") {
      return t("alerts.inventoryLow");
    }
    return title;
  }

  function formatAlertDescription(title: string, description: string) {
    if (title === "24h no follow-up") {
      return t("alerts.noFollowup24hDesc", { count: 6, country: formatCountry("Brazil", i18n.language) });
    }
    if (title === "Inventory low") {
      return t("alerts.inventoryLowDesc", { product: t("products.industrialCameraSku") });
    }
    return description;
  }

  return (
    <div className="page-stack">
      <section className="metric-grid">
        {metrics.map((metric) => (
          <MetricCard key={metric.labelKey} metric={metric} />
        ))}
      </section>

      <section className="grid two-columns">
        <article className="panel agent-summary">
          <div className="panel-heading">
            <h2>{t("overview.latestOwnerReport")}</h2>
            <span>{overview?.latest_report?.created_at ?? t("overview.generatedFromLocalFiles")}</span>
          </div>
          <p>
            {overview?.latest_report
              ? t("overview.latestReportReady", { title: t("reports.ownerDailyReport"), count: Number(overview.latest_report.summary?.files ?? 0) })
              : t("overview.noScheduledReport")}
          </p>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("overview.automationStatus")}</h2>
            <span>{overview?.active_automations.length ?? 0} {t("overview.rules")}</span>
          </div>
          <div className="list-stack">
            {(overview?.active_automations ?? []).slice(0, 4).map((rule) => (
              <article className="list-item" key={rule.id}>
                <div>
                  <strong>{rule.name === "Daily Owner Report" ? t("automations.dailyOwnerReport") : rule.name}</strong>
                  <span>{rule.next_run_at ? `${t("overview.next")}: ${rule.next_run_at}` : formatStatus(rule.status, t)}</span>
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
            <h2>{t("overview.recentSyncStatus")}</h2>
            <span>{t("overview.localConnectorJobs")}</span>
          </div>
          <div className="list-stack">
            {(overview?.recent_sync_jobs ?? []).map((job) => (
              <article className="list-item" key={job.id}>
                <div>
                  <strong>{formatStatus(job.status, t)}</strong>
                  <span>
                    {t("dataSources.recordsFound", { count: job.records_found })} / {t("dataSources.recordsImported", { count: job.records_imported })}
                  </span>
                </div>
              </article>
            ))}
            {!overview?.recent_sync_jobs.length ? <p className="muted">{t("overview.noConnectorJobs")}</p> : null}
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>{t("overview.openAlerts")}</h2>
            <span>{overview?.open_alerts.length ?? alerts.length} {t("overview.active")}</span>
          </div>
          {overview?.open_alerts.length ? (
            <div className="list-stack">
              {overview.open_alerts.map((alert) => (
                <article className="list-item" key={alert.id}>
                  <div>
                    <strong>{formatAlertTitle(alert.title)}</strong>
                    <span>{formatAlertDescription(alert.title, alert.description)}</span>
                  </div>
                  <StatusBadge label={formatSeverity(alert.severity, t)} tone={alert.severity === "high" ? "risk" : "warning"} />
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
          <h2>{t("dashboard.platformPerformance")}</h2>
          <span>{t("dashboard.mockedUntilConnected")}</span>
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
