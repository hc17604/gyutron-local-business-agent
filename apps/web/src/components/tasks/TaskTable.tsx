import { tasks } from "../../data/mockDashboard";
import { StatusBadge } from "../common/StatusBadge";

export function TaskTable() {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Task title</th>
            <th>Mode</th>
            <th>Status</th>
            <th>Created</th>
            <th>Completed</th>
            <th>Result summary</th>
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
