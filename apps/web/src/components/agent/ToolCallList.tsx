import { Wrench } from "lucide-react";

const tools = ["field_mapping.lookup", "business_rules.scan", "lead_ranker.run", "report_summary.build"];

export function ToolCallList() {
  return (
    <div className="tool-list">
      {tools.map((tool) => (
        <span key={tool}>
          <Wrench size={14} />
          {tool}
        </span>
      ))}
    </div>
  );
}
