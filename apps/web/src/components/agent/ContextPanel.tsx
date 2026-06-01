import { Activity, Code2, Database, FileText, ListChecks, ShieldCheck } from "lucide-react";

import { ToolCallList } from "./ToolCallList";

interface ContextPanelProps {
  workspaceRoot?: string;
  selectedProjectPaths?: string[];
  latestTools?: string[];
}

export function ContextPanel({ workspaceRoot, selectedProjectPaths = [], latestTools }: ContextPanelProps) {
  return (
    <aside className="context-panel">
      <div className="context-panel-head">
        <div>
          <p className="eyebrow">Agent context</p>
          <h3>Local workspace</h3>
        </div>
        <ShieldCheck size={18} />
      </div>
      <section>
        <h3>Selected business files</h3>
        <p>
          <FileText size={15} />
          alibaba_inquiries_may.csv
        </p>
        <p>
          <FileText size={15} />
          erp_orders_week22.xlsx
        </p>
      </section>
      <section>
        <h3>Selected project files</h3>
        {selectedProjectPaths.length ? (
          selectedProjectPaths.map((path) => (
            <p key={path}>
              <Code2 size={15} />
              {path}
            </p>
          ))
        ) : (
          <p className="muted">No project files selected</p>
        )}
        {workspaceRoot ? <p className="muted">Root: {workspaceRoot}</p> : null}
      </section>
      <section>
        <h3>Active business rules</h3>
        <p>
          <ListChecks size={15} />
          Brazil priority
        </p>
        <p>
          <ListChecks size={15} />
          24h no follow-up alert
        </p>
      </section>
      <section>
        <h3>Local memories used</h3>
        <p>
          <Database size={15} />
          Product focus: IC-420, BS-90
        </p>
      </section>
      <section>
        <h3><Activity size={14} /> Tools available</h3>
        <ToolCallList tools={latestTools} />
      </section>
    </aside>
  );
}
