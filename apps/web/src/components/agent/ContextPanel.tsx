import { Database, FileText, ListChecks } from "lucide-react";

import { ToolCallList } from "./ToolCallList";

export function ContextPanel() {
  return (
    <aside className="context-panel">
      <section>
        <h3>Selected files</h3>
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
        <h3>Tools available</h3>
        <ToolCallList />
      </section>
    </aside>
  );
}
