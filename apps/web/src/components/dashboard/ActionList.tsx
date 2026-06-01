import { ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";

import { formatStatus } from "../../i18n/formatters";
import type { ActionItem } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface ActionListProps {
  actions: ActionItem[];
}

export function ActionList({ actions }: ActionListProps) {
  const { t } = useTranslation();

  return (
    <div className="list-stack">
      {actions.map((action) => (
        <article className="list-item" key={action.titleKey}>
          <ArrowRight size={18} />
          <div>
            <strong>{t(action.titleKey)}</strong>
            <span>
              {t(action.ownerKey)} / {t(action.dueKey)}
            </span>
          </div>
          <StatusBadge label={formatStatus(action.priority, t)} tone={action.priority === "high" ? "risk" : "neutral"} />
        </article>
      ))}
    </div>
  );
}
