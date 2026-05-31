import { Wrench } from "lucide-react";

const defaultTools = [
  "llm.chat",
  "workspace_tree_tool",
  "file_read_tool",
  "file_search_tool",
  "patch_proposal_tool",
  "patch_apply_tool",
  "rollback_tool",
];

export function ToolCallList({ tools = defaultTools }: { tools?: string[] }) {
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
