import { ArrowRight } from "lucide-react";

import type { ActionItem } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface ActionListProps {
  actions: ActionItem[];
}

export function ActionList({ actions }: ActionListProps) {
  return (
    <div className="list-stack">
      {actions.map((action) => (
        <article className="list-item" key={action.title}>
          <ArrowRight size={18} />
          <div>
            <strong>{action.title}</strong>
            <span>
              {action.owner} · {action.due}
            </span>
          </div>
          <StatusBadge label={action.priority} tone={action.priority === "High" ? "risk" : "neutral"} />
        </article>
      ))}
    </div>
  );
}
