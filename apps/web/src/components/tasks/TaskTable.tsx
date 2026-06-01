import { useTranslation } from "react-i18next";

import { tasks } from "../../data/mockDashboard";
import { formatAutomationType, formatStatus } from "../../i18n/formatters";
import { StatusBadge } from "../common/StatusBadge";

export function TaskTable() {
  const { t } = useTranslation();

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{t("tasks.taskTitle")}</th>
            <th>{t("tasks.mode")}</th>
            <th>{t("common.status")}</th>
            <th>{t("tasks.created")}</th>
            <th>{t("tasks.completedAt")}</th>
            <th>{t("tasks.resultSummary")}</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.titleKey}>
              <td>{t(task.titleKey)}</td>
              <td>{formatAutomationType(task.mode, t)}</td>
              <td>
                <StatusBadge label={formatStatus(task.status, t)} tone={task.status === "completed" ? "success" : task.status === "running" ? "info" : "warning"} />
              </td>
              <td>{task.createdAt}</td>
              <td>{task.completedAt}</td>
              <td>{t(task.resultKey)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
