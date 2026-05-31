import { Pause, Play, Plus, RotateCw } from "lucide-react";
import { useEffect, useState } from "react";

import { createAutomation, getAutomations, pauseAutomation, resumeAutomation, runAutomation } from "../api/client";
import { PageHeader } from "../components/common/PageHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import type { AutomationRule } from "../types/api";

export function Automations() {
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
    setMessage("Daily Owner Report automation created.");
    await refresh();
  }

  async function run(id: number) {
    const result = await runAutomation(id);
    setMessage(result.summary ?? `Automation ${result.status}`);
    await refresh();
  }

  async function toggle(rule: AutomationRule) {
    if (rule.status === "active") {
      await pauseAutomation(rule.id);
      setMessage("Automation paused.");
    } else {
      await resumeAutomation(rule.id);
      setMessage("Automation resumed.");
    }
    await refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" onClick={createDailyReport} type="button">
            <Plus size={16} />
            Daily Owner Report
          </button>
        }
        description="Create lightweight local automations without turning GyuTron into a complex workflow builder."
        eyebrow="Local scheduler"
        title="Automations"
      />
      {message ? <div className="inline-info">{message}</div> : null}
      <section className="panel">
        <div className="panel-heading">
          <h2>Automation rules</h2>
          <span>Manual, scheduled, and data-updated triggers</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Trigger</th>
                <th>Action</th>
                <th>Status</th>
                <th>Next run</th>
                <th>Last run</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {automations.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.name}</td>
                  <td>{rule.schedule_cron ?? rule.trigger_type}</td>
                  <td>{rule.action_type}</td>
                  <td>
                    <StatusBadge label={rule.status} tone={rule.status === "active" ? "success" : "neutral"} />
                  </td>
                  <td>{rule.next_run_at ?? "-"}</td>
                  <td>{rule.last_run_at ?? "-"}</td>
                  <td>
                    <div className="table-actions">
                      <button className="table-action" onClick={() => void run(rule.id)} type="button">
                        <Play size={14} />
                        Run
                      </button>
                      <button className="table-action" onClick={() => void toggle(rule)} type="button">
                        {rule.status === "active" ? <Pause size={14} /> : <RotateCw size={14} />}
                        {rule.status === "active" ? "Pause" : "Resume"}
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
