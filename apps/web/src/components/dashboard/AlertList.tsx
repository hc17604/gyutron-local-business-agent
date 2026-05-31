import { AlertTriangle } from "lucide-react";

import type { AlertItem } from "../../types";
import { StatusBadge } from "../common/StatusBadge";

interface AlertListProps {
  alerts: AlertItem[];
}

export function AlertList({ alerts }: AlertListProps) {
  return (
    <div className="list-stack">
      {alerts.map((alert) => (
        <article className="list-item" key={alert.title}>
          <AlertTriangle size={18} />
          <div>
            <strong>{alert.title}</strong>
            <span>{alert.summary}</span>
          </div>
          <StatusBadge label={alert.severity} tone={alert.severity === "High" ? "risk" : "warning"} />
        </article>
      ))}
    </div>
  );
}
