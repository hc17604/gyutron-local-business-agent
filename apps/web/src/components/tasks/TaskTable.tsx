import { useTranslation } from "react-i18next";

import { tasks } from "../../data/mockDashboard";
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
            <tr key={task.title}>
              <td>{task.title}</td>
              <td>{task.mode}</td>
              <td>
                <StatusBadge label={task.status} tone={task.status === "Completed" ? "success" : task.status === "Running" ? "info" : "warning"} />
              </td>
              <td>{task.createdAt}</td>
              <td>{task.completedAt}</td>
              <td>{task.result}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
