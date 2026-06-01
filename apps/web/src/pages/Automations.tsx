import { Pause, Play, Plus, RotateCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { createAutomation, getAutomations, pauseAutomation, resumeAutomation, runAutomation } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { formatAutomationType, formatStatus } from "../i18n/formatters";
import type { AutomationRule } from "../types/api";

export function Automations() {
  const { t } = useTranslation();
  const [automations, setAutomations] = useState<AutomationRule[]>([]);
  const [message, setMessage] = useState<string>();

  async function refresh() {
    const response = await getAutomations();
    setAutomations(response.automations);
  }

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
  }, []);

  async function createDailyReport() {
    await createAutomation({
      name: "Daily Owner Report",
      description: "Generate a local owner report every morning.",
      trigger_type: "schedule",
      schedule_cron: "daily:09:00",
      action_type: "generate_report",
      action_config_json: {},
    });
    setMessage(t("automations.dailyCreated"));
    await refresh();
  }

  async function run(id: number) {
    const result = await runAutomation(id);
    setMessage(result.summary ?? `${t("automations.title")} ${formatStatus(result.status, t)}`);
    await refresh();
  }

  async function toggle(rule: AutomationRule) {
    if (rule.status === "active") {
      await pauseAutomation(rule.id);
      setMessage(t("automations.paused"));
    } else {
      await resumeAutomation(rule.id);
      setMessage(t("automations.resumed"));
    }
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" onClick={createDailyReport} type="button">
            <Plus size={16} />
            {t("automations.dailyOwnerReport")}
          </button>
        }
        description={t("automations.description")}
        eyebrow={t("automations.eyebrow")}
        title={t("automations.title")}
      />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="panel-heading">
          <h2>{t("automations.automationRules")}</h2>
          <span>{t("automations.ruleDescription")}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t("dataSources.name")}</th>
                <th>{t("automations.trigger")}</th>
                <th>{t("automations.action")}</th>
                <th>{t("common.status")}</th>
                <th>{t("automations.nextRun")}</th>
                <th>{t("automations.lastRun")}</th>
                <th>{t("common.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {automations.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.name === "Daily Owner Report" ? t("automations.dailyOwnerReport") : rule.name}</td>
                  <td>{rule.schedule_cron ?? formatAutomationType(rule.trigger_type, t)}</td>
                  <td>{formatAutomationType(rule.action_type, t)}</td>
                  <td>
                    <StatusBadge label={formatStatus(rule.status, t)} tone={rule.status === "active" ? "success" : "neutral"} />
                  </td>
                  <td>{rule.next_run_at ?? "-"}</td>
                  <td>{rule.last_run_at ?? "-"}</td>
                  <td>
                    <div className="table-actions">
                      <button className="table-action" onClick={() => void run(rule.id)} type="button">
                        <Play size={14} />
                        {t("automations.runNow")}
                      </button>
                      <button className="table-action" onClick={() => void toggle(rule)} type="button">
                        {rule.status === "active" ? <Pause size={14} /> : <RotateCw size={14} />}
                        {rule.status === "active" ? t("automations.pause") : t("automations.resume")}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
