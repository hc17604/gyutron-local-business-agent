import { PageHeader } from "../components/common/PageHeader";
import { TaskTable } from "../components/tasks/TaskTable";

export function Tasks() {
  return (
    <div className="page-stack">
      <PageHeader
        description="Track Agent tasks, report generation jobs, tool calls, results, errors, and audit trails."
        eyebrow="Execution center"
        title="Tasks"
      />
      <section className="panel">
        <div className="panel-heading">
          <h2>Task history</h2>
          <span>Mocked until AgentTask API is connected</span>
        </div>
        <TaskTable />
      </section>
    </div>
  );
}
