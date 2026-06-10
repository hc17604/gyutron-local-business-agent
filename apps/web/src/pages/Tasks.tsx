import { CheckCircle2, RefreshCw, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { evaluateRulesNow, getTasks, updateTask } from "../api/client";
import { EmptyState } from "../components/common/EmptyState";
import { PageHeader } from "../components/common/PageHeader";
import { SectionHeader } from "../components/common/SectionHeader";
import { StatusBadge } from "../components/common/StatusBadge";
import { formatStatus } from "../i18n/formatters";
import type { AgentTask } from "../types/api";

export function Tasks() {
  const { t } = useTranslation();
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [statusFilter, setStatusFilter] = useState<string>("open");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [message, setMessage] = useState<string>();

  async function refresh(status = statusFilter, priority = priorityFilter) {
    const response = await getTasks({ status: status || undefined, priority: priority || undefined });
    setTasks(response.tasks);
    setCounts(response.counts);
  }

  useEffect(() => {
    refresh().catch((error: Error) => setMessage(error.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, priorityFilter]);

  async function handleStatus(task: AgentTask, status: string) {
    await updateTask(task.id, status);
    await refresh();
  }

  async function handleEvaluate() {
    const result = await evaluateRulesNow();
    setMessage(t("tasks.evaluateResult", { created: result.tasks_created, closed: result.tasks_auto_closed }));
    await refresh();
  }

  const tone = (priority: string) => (priority === "high" ? "warning" : priority === "low" ? "neutral" : "info");

  return (
    <div className="page-stack">
      <PageHeader
        actions={
          <button className="button primary" onClick={() => void handleEvaluate().catch((error: Error) => setMessage(error.message))} type="button">
            <RefreshCw size={16} />
            {t("tasks.evaluateNow")}
          </button>
        }
        description={t("tasks.description")}
        eyebrow={t("tasks.eyebrow")}
        title={t("tasks.title")}
      />
      {message ? <div className="inline-info">{message}</div> : null}

      <section className="panel">
        <SectionHeader
          title={t("tasks.taskList")}
          meta={`${counts.open ?? 0} ${formatStatus("open", t)} · ${counts.done ?? 0} ${formatStatus("done", t)}`}
        />
        <div className="table-actions" style={{ marginBottom: 12 }}>
          <label>
            {t("common.status")}
            <select onChange={(event) => setStatusFilter(event.target.value)} value={statusFilter}>
              <option value="">{t("tasks.all")}</option>
              <option value="open">{formatStatus("open", t)}</option>
              <option value="in_progress">{formatStatus("in_progress", t)}</option>
              <option value="done">{formatStatus("done", t)}</option>
              <option value="dismissed">{formatStatus("dismissed", t)}</option>
            </select>
          </label>
          <label>
            {t("tasks.priority")}
            <select onChange={(event) => setPriorityFilter(event.target.value)} value={priorityFilter}>
              <option value="">{t("tasks.all")}</option>
              <option value="high">{formatStatus("high", t)}</option>
              <option value="medium">{formatStatus("medium", t)}</option>
              <option value="low">{formatStatus("low", t)}</option>
            </select>
          </label>
        </div>
        {tasks.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t("tasks.taskTitle")}</th>
                  <th>{t("tasks.priority")}</th>
                  <th>{t("common.status")}</th>
                  <th>{t("tasks.entity")}</th>
                  <th>{t("tasks.rule")}</th>
                  <th>{t("tasks.created")}</th>
                  <th>{t("common.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <strong>{task.title}</strong>
                      {task.description ? <div className="muted">{task.description}</div> : null}
                    </td>
                    <td>
                      <StatusBadge label={formatStatus(task.priority, t)} tone={tone(task.priority)} />
                    </td>
                    <td>
                      <StatusBadge label={formatStatus(task.status, t)} tone={task.status === "open" ? "warning" : task.status === "done" ? "success" : "neutral"} />
                    </td>
                    <td>{task.entity_id ?? "-"}</td>
                    <td>{task.rule_id ?? "-"}</td>
                    <td>{task.created_at}</td>
                    <td>
                      {task.status === "open" || task.status === "in_progress" ? (
                        <div className="table-actions">
                          <button className="table-action" onClick={() => void handleStatus(task, "done").catch((error: Error) => setMessage(error.message))} type="button">
                            <CheckCircle2 size={14} />
                            {t("tasks.markDone")}
                          </button>
                          <button className="table-action" onClick={() => void handleStatus(task, "dismissed").catch((error: Error) => setMessage(error.message))} type="button">
                            <XCircle size={14} />
                            {t("tasks.dismiss")}
                          </button>
                        </div>
                      ) : (
                        "-"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title={t("tasks.noTasks")} description={t("tasks.noTasksDescription")} />
        )}
      </section>
    </div>
  );
}
