import { Wrench } from "lucide-react";
import { useTranslation } from "react-i18next";

import { formatToolName } from "../../i18n/formatters";

const defaultTools = [
  "llm.chat",
  "workspace_tree_tool",
  "file_read_tool",
  "file_search_tool",
  "patch_proposal_tool",
  "patch_apply_tool",
  "rollback_tool",
  "connector_list_tool",
  "connector_sync_tool",
  "automation_create_tool",
  "automation_run_tool",
  "automation_pause_tool",
  "alert_list_tool",
  "report_latest_tool",
];

export function ToolCallList({ tools = defaultTools }: { tools?: string[] }) {
  const { t } = useTranslation();

  return (
    <div className="tool-list">
      {tools.map((tool) => (
        <span key={tool}>
          <Wrench size={14} />
          <strong>{formatToolName(tool, t)}</strong>
          <small>{tool}</small>
        </span>
      ))}
    </div>
  );
}
